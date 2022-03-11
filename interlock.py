#!/usr/bin/python
#-*- coding: latin-1 -*-

import RPi.GPIO as GPIO
import atexit

import omron_ups

class Interlock (object):
    """Represent the interlock system of the oven setup. The interlock consists of four parts
    - cooling water (Is the cooling water flowing?)
    - temperature check (Is no temperature too high and are the thermocouples OK?)
    - powersupply check (Are the powersupplies responsive and within their maximum values?)
    - UPS check (Is there no power outage and the health status of all UPS is fine?)
    """

    ALL_OK = 0      # no interlock issues detected
    WATER_FAIL = 1  # water flow sensor fail
    TEMP_FAIL = 2   # some temperature reading too high
    HEATER_FAIL = 4 # some heater resistance too high or too low
    PSU_FAIL = 8    # communication failure with a power supply
    UPS_FAIL = 16   # power outage or error condition reported by UPS

    def __init__ (self, configuration, shmem_temperatures, shmem_currents, shmem_voltages):
        """Object initialization.

        :param configuration: global configuration object
        :param shmem_temperatures: list with current temperatures
        :param shmem_currents: list with current currents
        :param shmem_voltages: list with current voltages
        """

        self.config = configuration
        self.temperatures = shmem_temperatures
        self.currents = shmem_currents
        self.voltages = shmem_voltages

        self.water_interlock_pin = int (self.config.getGeneral ('water_interlock_pin'))
        GPIO.setmode (GPIO.BCM)
        GPIO.setup (self.water_interlock_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

        self.status = Interlock.ALL_OK
        self.details = None

        # counter and limit for temperature violations
        # that is to not react to spurious spikes in the temperature readings
        self.temp_fail_count = 0
        self.temp_fail_max   = 3

        # counter and limit for heater resistance violations
        # that is to discard inaccurate readings right after PSU changes from 0 A
        self.heater_fail_count = 0
        self.heater_fail_max   = 3

        # list of UPS ip adresses to be checked
        self.ups_IPs = self.config.getUPSInfo ()
        self.UPSs = [omron_ups.OmronUPS (ip) for ip in self.ups_IPs]
        # Checking the UPS status is done via an HTTP request and computational
        # wise quite expensive. We choose to check the UPS only once every few
        # runs. (Remember that the interlock update is run once per second.)
        self.ups_update_interval = 10
        self.ups_update_interval_count = 0
        # similar to above we also allow the UPS to fail for a short time
        self.ups_fail_count = 0
        self.ups_fail_max = 6

        atexit.register (self.cleanup)

    def cleanup (self):
        """Free GPIO pin on object destruction"""

        GPIO.cleanup (self.water_interlock_pin)

    def update (self):
        """Update interlock status"""

        # cooling water
        if GPIO.input (self.water_interlock_pin) == GPIO.HIGH:
            self.status |= Interlock.WATER_FAIL
            self.details = 'Cooling water flow failure'
        else:
            self.status &= ~Interlock.WATER_FAIL

        # temperatures
        failed = False
        for pos, sensor in enumerate (self.config.getThermocoupleNames ()):
            # below maximum temperature?
            if self.temperatures[pos] > self.config.getThermocouple (sensor)['max_temp']:
                # at first only increase failure counter
                self.temp_fail_count += 1
                if self.temp_fail_count > self.temp_fail_max:
                    # consistently above temperature limit --> activate interlock
                    self.status |= Interlock.TEMP_FAIL
                    self.details = 'Temperature at thermocouple\n"{}" above set maximum'.format(self.config.getThermocouple (sensor)['name'])
                    failed = True
            # sensor works correctly?
            if self.temperatures[pos] < 0:
                self.status |= Interlock.TEMP_FAIL
                self.details = 'Thermocouple "{}"\n failure'.format(self.config.getThermocouple (sensor)['name'])
                failed = True
        if not failed:
            self.status &= ~Interlock.TEMP_FAIL
            self.temp_fail_count = 0

        # heater resistances
        failed = False
        for pos, psu in enumerate (self.config.getPowersupplyNames ()):
            if self.currents[pos] < -0.9 or self.voltages[pos] < -0.9:
                # either current or voltage are not properly measured
                continue
            # current at least above 0.2 A to get a sensible resistance estimate?
            if self.currents[pos] > 0.2 or self.voltages[pos] > 2.0:
                if self.currents[pos] <= 0.001:
                    # prevent basically division-by-zero errors
                    resistance = 1e6
                else:
                    resistance = self.voltages[pos] / self.currents[pos]
                if not (0.2 < resistance < 50.0):
                    # heater resistance out of safe range

                    # at first only increase failure counter
                    self.heater_fail_count += 1
                    if self.heater_fail_count > self.heater_fail_max:
                        self.status |= Interlock.HEATER_FAIL
                        #print("voltage: ", self.voltages[pos])
                        #print("current: ", self.currents[pos])
                        #print("resistance: ", resistance)
                        #print("")

                        # determine the name of the heater corresponding to this powersupply
                        psu_name = self.config.getPowersupply (psu)['name']
                        heater_name = 'unknown'
                        for heater in self.config.getHeaterNames ():
                            heater_info = self.config.getHeater (heater)
                            if heater_info['powersupply'] == psu_name:
                                heater_name = heater_info['name']

                        self.details = 'Resistance of heater "{}",\n{:.1f} V / {:.1f} A = {:.1f} Ohm,\nout of range'.\
                                       format(heater_name, self.voltages[pos], self.currents[pos], resistance)
                        failed = True
        if not failed:
            self.status &= ~Interlock.HEATER_FAIL
            self.heater_fail_count = 0

        # powersupplies
        failed = False
        for pos, psu in enumerate (self.config.getPowersupplyNames ()):
            # current below maximum?
            if self.currents[pos] > self.config.getPowersupply (psu)['max_current']:
                self.status |= Interlock.PSU_FAIL
                self.details = 'Powersupply "{}" overcurrent'.format(self.config.getPowersupply (psu)['name'])
                failed = True
            # powersupply responsive?
            if self.currents[pos] < -0.1:
                self.status |= Interlock.PSU_FAIL
                self.details = 'Powersupply "{}" communication failure'.format(self.config.getPowersupply (psu)['name'])
                failed = True
        if not failed:
            self.status &= ~Interlock.PSU_FAIL

        # UPS
        if self.ups_update_interval_count == 0:
            failed = False
            all_ups_fine = True
            # query status of each UPS
            for ups in self.UPSs:
                ups_status = ups.getInterlock ()
                if not ups_status[0]:
                    # UPS fault condition
                    self.ups_fail_count += 1
                    # remember that there is a UPS with trouble
                    all_ups_fine = False
                    if self.ups_fail_count > self.ups_fail_max:
                        # UPS returns error for a longer time --> activate interlock
                        self.status |= Interlock.UPS_FAIL
                        self.details = "UPS: " + ups_status[1]
                        failed = True
                    # skip checking the remaining UPS in this run
                    continue
            if not failed:
                self.status &= ~Interlock.UPS_FAIL
            if all_ups_fine:
                # reset counter only if there is no UPS with trouble
                self.ups_fail_count = 0

        # advance UPS check counter
        self.ups_update_interval_count += 1
        if self.ups_update_interval_count == self.ups_update_interval:
            self.ups_update_interval_count = 0
