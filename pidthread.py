#!/usr/bin/python
#-*- coding: latin-1 -*-

import time
import threading
import Queue

import heater
import PID

class PIDthread (threading.Thread):
    """Worker thread to manage the PIDs"""

    def __init__ (self, shmem_temperatures, shmem_current_setpoints, shmem_currents, configuration, queue):
        """Set up the PIDthread object.

        :param shmem_temperatures: shared memory of current temperatures
        :param shmem_current_setpoints: shared memory for current feedback
        :param shmem_currents: shared memory for currently measured currents
        :param configuration: global configuration object
        :param queue: message queue
        """
        threading.Thread.__init__ (self)

        self.shmem_temperatures = shmem_temperatures
        self.shmem_current_setpoints = shmem_current_setpoints
        self.shmem_currents = shmem_currents
        self.config = configuration
        self.queue = queue

        # Special flag we set in the main program for a ramp to off
        # This is so that the powersupplies will be turned off once the
        # target temperature has been reached or the current is alreay zero.
        self.ramp_to_off = False

        # Build a dictionary that gives the array positions of the thermocouples and powersupplies
        self.thermocouple_pos = {}
        for pos, name in enumerate (self.config.getThermocoupleNames ()):
            self.thermocouple_pos[name] = pos
        self.powersupply_pos = {}
        for pos, name in enumerate (self.config.getPowersupplyNames ()):
            self.powersupply_pos[name] = pos

        # Limit maximum temperature difference during ramp up
        self.ramp_up_max_temp_delta = float (self.config.getGeneral ('ramp_up_max_temp_delta'))

        # Heater objects and PIDs
        self.heaters = {}
        self.PIDs = {}
        for heatername in self.config.getHeaterNames ():
            self.heaters[heatername] = heater.Heater (
                    self.config.getHeater (heatername),
                    state = 'o',
                    target = -1,
                    setpoint = -1
                    )
            self.PIDs[heatername] = PID.PID (
                    self.heaters[heatername].info['low_pid_p'] / 1000.,
                    self.heaters[heatername].info['low_pid_i'] / 1000.,
                    self.heaters[heatername].info['low_pid_d'] / 1000.,
                    )
            self.PIDs[heatername].setSampleTime (
                    float (self.config.getGeneral ('pid_update_interval'))
                    )
            self.PIDs[heatername].setWindup (
                    self.config.getPowersupply (self.heaters[heatername].info['powersupply'])['max_current']
                    )
            self.PIDs[heatername].setOutputLimits (
                    0,
                    self.config.getPowersupply (self.heaters[heatername].info['powersupply'])['max_current'] - 0.05
                    )
            self.PIDs[heatername].output = -1

        # PID stability status storage
        self.PIDstability = {}
        for heatername in self.config.getHeaterNames ():
            self.PIDstability[heatername] = {}
            self.PIDstability[heatername]['stable'] = False                   # True if heater considered stable 
            self.PIDstability[heatername]['stability_threshold'] = 0.3        # Consider stable if heater temperature error below threshold
            self.PIDstability[heatername]['below_threshold_since'] = None     # Timestamp when the error got below the threshold
            self.PIDstability[heatername]['time_threshold'] = 120             # Time in s below threshold for heater to become stable
            self.PIDstability[heatername]['back-off_factor'] = 2              # Roughly the factor by which the loop time constant of a stable PID is increased
            self.PIDstability[heatername]['startup_check'] = False            # Whether to check for startup mode at all
            self.PIDstability[heatername]['startup_mode'] = False             # Whether the heater is currently in startup mode
            self.PIDstability[heatername]['startup_threshold'] = 50           # Temperature below which reduced startup PID values are used
            self.PIDstability[heatername]['startup_PID_back-off'] = 4         # Increase factor of PID loop time constant for startup
            self.PIDstability[heatername]['startup_ramp_factor'] = 0.33       # Multiplicative factor of the ramp speed during startup
            self.PIDstability[heatername]['startup_max_current_factor'] = 0.5 # Multiplicative factor of the maximum heater current during startup

    def run (self):
        """Start main loop of PID thread"""

        time_last = time.time ()
        while True:

            # update temperature setpoints once a second
            time_now = time.time ()
            time_delta = time_now - time_last
            if time_delta > 1.0:
                for heatername, heater in self.heaters.items ():
                    if heater.state == 'a':
                        # normal case ramp
                        temp_delta = heater.info['ramp_speed'] * time_delta/60.
                    elif heater.state == 'e':
                        # in case of emergency use a different ramp speed
                        temp_delta = heater.info['emergency_ramp_speed'] * time_delta/60.
                    else:
                        # oven in frozen state or otherwise not running
                        continue
                    # update PID settings
                    self.PIDs[heatername] = self.PIDsettingsInterpolate (self.PIDs[heatername], heater)
                    # update heater stability status and back-off PID gain when stable
                    self._updateStability (heater)
                    if self.PIDstability[heatername]['stable'] == True:
                        self.PIDs[heatername].Kp /= self.PIDstability[heatername]['back-off_factor']
                        self.PIDs[heatername].Ki /= self.PIDstability[heatername]['back-off_factor']**2
                        #print "backed-off PID parameters for heater {}".format(heatername)
                    else:
                        # check whether special startup treatment is necessary
                        if self._checkStartup (heater) == True:
                            # invoke startup PID settings to adjust PID settings and ramp speed
                            self.PIDs[heatername].Kp /= self.PIDstability[heatername]['startup_PID_back-off']
                            self.PIDs[heatername].Ki /= self.PIDstability[heatername]['startup_PID_back-off']**2
                            temp_delta *= self.PIDstability[heatername]['startup_ramp_factor']
                            self.PIDstability[heatername]['startup_mode'] = True
                        else:
                            # currently outside of startup mode
                            if self.PIDstability[heatername]['startup_mode']:
                                # we were in startup mode up to now
                                # --> to make the transition to normal operation as smooth as
                                # possible reset the temperature setpoint to current temperature ...
                                thermocouplepos = self.thermocouple_pos[heater.info['thermocouple']]
                                heater.setpoint = self.shmem_temperatures[thermocouplepos]
                                # ... and clear the PID once (this triggers the clear routine further below)
                                self.PIDs[heatername].output = -1.
                                # remember that we are out of startup_mode
                                self.PIDstability[heatername]['startup_mode'] = False
                    # update temperature setpoint
                    if heater.setpoint >= 0. and heater.setpoint < heater.target:
                        # ramp up temperature
                        thermocouplepos = self.thermocouple_pos[heater.info['thermocouple']]
                        current_heater_temp = self.shmem_temperatures[thermocouplepos]
                        if heater.setpoint - current_heater_temp > self.ramp_up_max_temp_delta:
                            # the difference between setpoint and actual temperature has become
                            # quite large -> do not further increase the setpoint to prevent
                            # integrator windup of the PID and to give the heater some time to
                            # catch up with the setpoint temperature
                            temp_delta = 0.
                        heater.setpoint = min (heater.target, heater.setpoint + temp_delta)
                    if heater.setpoint >= 0. and heater.setpoint > heater.target:
                        # ramp down temperature
                        heater.setpoint = max (heater.target, heater.setpoint - temp_delta)

                time_last = time_now

            # run PIDs on active heaters
            for heatername, heater in self.heaters.items ():
                if heater.setpoint < 0:
                    # No setpoint defined for this heater -> skip
                    continue

                if heater.state == 'a' or heater.state == 'e':
                    thermocouplepos = self.thermocouple_pos[heater.info['thermocouple']]
                    powersupplypos = self.powersupply_pos[heater.info['powersupply']]

                    if (self.PIDs[heatername].output < -0.5):
                        # This PID just got started, better reset it
                        self.PIDs[heatername].clear ()
                        # Precondition integral term for bumpless start
                        if self.shmem_currents[powersupplypos] >= 0:
                            # use available powersupply reading as initial value
                            self.PIDs[heatername].ITerm = self.shmem_currents[powersupplypos]
                            # also update the current setpoint so that the "limit rate of current change"
                            # algorithm below can work correctly
                            self.shmem_current_setpoints[powersupplypos] = self.shmem_currents[powersupplypos]
                        else:
                            # no powersupply value available, so use last setpoint
                            self.PIDs[heatername].ITerm = self.shmem_current_setpoints[powersupplypos]

                    # We have an active heater, so let's update the temperature setpoint and PID
                    self.PIDs[heatername].SetPoint = self.heaters[heatername].setpoint
                    self.PIDs[heatername].update (self.shmem_temperatures[thermocouplepos])

                    if self.shmem_current_setpoints[powersupplypos] == self.PIDs[heatername].output:
                        # Nothing changed, skip the rest
                        continue

                    # Limit rate of current change between successive PID updates
                    if (abs (self.PIDs[heatername].output - self.shmem_current_setpoints[powersupplypos]) >
                                    float (self.config.getGeneral ('max_current_change'))):
                        # change of current too large, now determine the direction of change and clip
                        if self.PIDs[heatername].output > self.shmem_current_setpoints[powersupplypos]:
                            # clip increase of current
                            self.PIDs[heatername].output = self.shmem_current_setpoints[powersupplypos] + \
                                    float (self.config.getGeneral ('max_current_change'))
                        else:
                            # clip decrease of current
                            self.PIDs[heatername].output = self.shmem_current_setpoints[powersupplypos] - \
                                    float (self.config.getGeneral ('max_current_change'))

                    # Limit current (the PID routine should already take care of the limits, but just in case...)
                    # For the upper limit leave 0.05 A of margin as the powersupply sometimes deliveres a bit more than the set value
                    if self.PIDs[heatername].output < 0:
                        self.PIDs[heatername].output = 0.
                    max_current = self.config.getPowersupply (self.heaters[heatername].info['powersupply'])['max_current']

                    # Limit current even stronger when in startup mode
                    if self.PIDstability[heatername]['startup_mode']:
                        max_current *= self.PIDstability[heatername]['startup_max_current_factor']

                    # Clip current to the maximum current (plus a security margin of 50 mA)
                    if self.PIDs[heatername].output > max_current - 0.05:
                        self.PIDs[heatername].output = max_current - 0.05

                    # In case of a "ramp to off": set currents to zero for those powersupplies
                    # where we are already at target # or the PID output became zero anyway
                    if self.ramp_to_off == True:
                        #if self.shmem_current_setpoints[powersupplypos] < 0.02:
                        #    # current was (nearly) zero in last loop iteration, so make sure that the
                        #    # current won't ramp up again (by falling below the off temperature)
                        #    self.PIDs[heatername].output = 0.;
                        #    self.PIDs[heatername].setpoint = -1;
                        if self.shmem_temperatures[thermocouplepos] <= float (self.config.getGeneral ('off_state_temperature')):
                            # oven already cold enough to be set to zero
                            self.PIDs[heatername].output = 0.;
                            self.PIDs[heatername].setpoint = -1;

                    # Propagate the computed current from the PID to the powersupply
                    self.shmem_current_setpoints[powersupplypos] = self.PIDs[heatername].output

            # check whether there is a message from the parent process
            try:
                message = self.queue.get_nowait ()
                if message == 'q':
                    # parent is about to quit
                    return True
            except Queue.Empty:
                pass

            time.sleep (0.100)

    def PIDsettingsInterpolate (self, PID, heater):
        """Based on the PID settings for the low and high temperature interpolate
        the PID settings at the current setpoint

        :param PID: PID object to be updated
        :param heater: heater object with temperature and setpoint information
        :return: modified PID object
        """

        # clip temperature to be between the LOW and the HIGH set temperatures
        x = max (heater.info['temp_low'], min (heater.info['temp_high'], heater.setpoint))

        tl = heater.info['temp_low']
        th = heater.info['temp_high']

        PID.Kp = self._interpolation (tl, heater.info['low_pid_p'], th, heater.info['high_pid_p'], x) / 1000.
        PID.Ki = self._interpolation (tl, heater.info['low_pid_i'], th, heater.info['high_pid_i'], x) / 1000.
        PID.Kd = self._interpolation (tl, heater.info['low_pid_d'], th, heater.info['high_pid_d'], x) / 1000.

        return PID

    def _interpolation (self, x0, y0, x1, y1, x):
        """Helper function to do interpolation between two points

        :param X0, y0: first known point
        :param x1, y1: second known point
        :param x: point of interest for interpolation
        :return: y value at x
        """
        return y0 + (x - x0) * (y1 - y0)/(x1 - x0)

    def _updateStability (self, heater):
        """Helper function to set the stability status of a heater
        A heater is considered stable if no ramp is running and the temperature
        error is below a given threshold for a certain amount of time.
        A heater is becoming unstable if a ramp is running.

        :param heater: heater object to be updated
        """

        name = heater.info['name']

        if (heater.setpoint < 0):
            # heater is not active, assume it to be not stable
            self.PIDstability[name]['stable'] = False
            self.PIDstability[name]['below_threshold_since'] = None
            return

        if (heater.setpoint != heater.target):
            # setpoint and target differ, therefore we are ramping
            # and the heater is per definition not stable
            self.PIDstability[name]['stable'] = False
            self.PIDstability[name]['below_threshold_since'] = None
            #print "heater {} stability: False (ramp is running)".format(name)
            return

        # No ramp is active, make heater stable if long enough below the
        # temperature threshold for stability.

        thermocouplepos = self.thermocouple_pos[heater.info['thermocouple']]

        if (abs (self.shmem_temperatures[thermocouplepos] - heater.setpoint) <
                self.PIDstability[name]['stability_threshold']):
            # below temperature threshold for stability
            now = time.time ()
            if self.PIDstability[name]['below_threshold_since'] == None:
                # first time below threshold
                self.PIDstability[name]['below_threshold_since'] = now
                #print "heater {} stability: {} (but first time below threshold)".format(name, self.PIDstability[name]['stable'])
            else:
                # was below threshold before
                if (now - self.PIDstability[name]['below_threshold_since'] >
                        self.PIDstability[name]['time_threshold']):
                    # long enough below threshold to become stable
                    self.PIDstability[name]['stable'] = True
                    #print "heater {} stability: True".format(name)
                #else:
                    #print "heater {} stability: {} (but below threshold since {} s)".format(name, self.PIDstability[name]['stable'], now - self.PIDstability[name]['below_threshold_since'])
        else:
            # above temperature threshold for stability
            #
            # note: We do not set the stability flag itself to False. That can
            # only be triggered by a ramp. Therefore, once we reach stability
            # temperature spikes of the sensor won't cause the system to reset
            # its stability status. That was the whole point, to get a soft PID
            # response that won't react to sensor noise.
            self.PIDstability[name]['below_threshold_since'] = None
            #print "heater {} stability: {} (and above threshold)".format(name, self.PIDstability[name]['stable'])

    def _checkStartup (self, heater):
        """Helper function to whether a heater is in its startup phase.
        A heater is considered to be during startup if its temperature
        is below the startup_threshold temperature of that heater

        :param heater: heater object to be checked
        :return: True if startup phase detected, false otherwise
        """

        name = heater.info['name']
        thermocouplepos = self.thermocouple_pos[heater.info['thermocouple']]

        if self.PIDstability[name]['startup_check'] == False:
            # the startup_check flag is not set so by definition we shall
            # not be in startup mode
            return False

        if self.shmem_temperatures[thermocouplepos] < self.PIDstability[name]['startup_threshold']:
            # we should enter startup mode
            return True
        else:
            # we should not enter startup mode
            # Also set the startup_check flag to False as to prevent further checks
            # that might re-enable start mode by spurious fluctuations of the temperature.
            self.PIDstability[name]['startup_check'] = False
            return False
