#!/usr/bin/python
#-*- coding: latin-1 -*-
"""Main file for ErYbLi-oven control program."""

import numpy
import multiprocessing
from datetime import datetime
#from threading import Thread, Timer
#import time
import paho.mqtt.client as mqtt
import json

import wx
import matplotlib
matplotlib.use ('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

from controlGUI import ControlGUI
import configuration
import thermocouple
import thermocouple_process
import takasago
import powersupply_process
import interlock
import pidthread
#import heater
#import PID
import mailsystem
import buzzer
import logging_mysql as logger

# start by loading the main configuration file into the global config
config = configuration.Configuration ()
config.load ()

class MainWindow (ControlGUI):
    """ErYbLi-oven control program main window functions"""

    def __init__ (self, *args, **kwds):
        """Define the application

        This includes
        - setting up the GUI
        - initializing the thermocouple object
        - initializing the powersupply object
        """
        ControlGUI.__init__ (self, *args, **kwds)

        # important variables
        self.totalramptime = 0
        self.oven_status = 'idle'
        self.automatic_startup = None
        self.oven_buttonlist = [self.button_ramp_high,
                                self.button_ramp_low,
                                self.button_ramp_off,
                                self.button_ramp_emergency]

        # thermocouples
        # We need to maintain a list of installed but not used, i.e. 'inactive'
        # thermocouples. Those need to be enabled anyway, such that their chip select
        # pin is pulled to high. Otherwise the chips won't be inactive and interfere
        # with the actually used thermocouples' data output.
        tc_complete_list = [int (pin) for pin in config.getGeneral('thermocouple_pins').split (',')]
        self.thermocouples = {}
        for pos, tc in enumerate (config.getThermocoupleNames ()):
            # configure 'active' thermocouples
            self.thermocouples[tc] = thermocouple.Thermocouple (
                    type = config.getThermocouple (tc)['type'],
                    pin = config.getThermocouple (tc)['pin'],
                    position = pos
                    )
            tc_complete_list = filter (lambda pin: pin != config.getThermocouple (tc)['pin'], tc_complete_list)
        self.thermocouples_inactive = {}
        for pin in tc_complete_list:
            # configure 'inactive' thermocouples
            self.thermocouples_inactive[pin] = thermocouple.Thermocouple (
                    pin = pin
                    )

        # powersupplies
        self.powersupplies = {}
        for pos, psu in enumerate (config.getPowersupplyNames ()):
            self.powersupplies[psu] = takasago.TakasagoPowersupply (
                    device = config.getGeneral ('serial_device'),
                    address = config.getPowersupply (psu)['address'],
                    max_current = config.getPowersupply (psu)['max_current'],
                    model = config.getPowersupply (psu)['model'],
                    position = pos
                    )

        # set up shared memory space to hold latest process values and message queues
        self.shmem_temperatures = multiprocessing.Array ('f', len (self.thermocouples))
        self.shmem_currents = multiprocessing.Array ('f', len (self.powersupplies))
        self.shmem_voltages = multiprocessing.Array ('f', len (self.powersupplies))
        self.shmem_current_setpoints = multiprocessing.Array ('f', len (self.powersupplies))
        self.queue_temperatures = multiprocessing.Queue ()
        self.queue_powersupplies = multiprocessing.Queue ()

        # now that we have the shared variables, set up the interlock
        self.interlock = interlock.Interlock (config, self.shmem_temperatures, self.shmem_currents, self.shmem_voltages)
        self.interlock_oldstatus = -1
        self.interlock_is_critical = False
        self.interlock_is_critical_oldstate = False
        self.interlock_ignore_mask = 0 # bitmask of interlocks to be ignored
        self.buzzer = buzzer.Buzzer (int (config.getGeneral ('buzzer_pin')))

        # populate initial temperature and currents
        for sensor in self.thermocouples:
            pos = self.thermocouples[sensor].position
            try:
                temptry = self.thermocouples[sensor].updateBothTemperatures ()
                if temptry != None:
                    self.shmem_temperatures[pos] = self.thermocouples[sensor].correctTemperature (temptry['sensor'], temptry['rj'])
                else:
                    self.shmem_temperatures[pos] = -1
            except TypeError:
                self.shmem_temperatures[pos] = -1
        for psu in self.powersupplies:
            pos = self.powersupplies[psu].position
            try:
                self.shmem_currents[pos] = self.powersupplies[psu].getCurrent ()
            except TypeError:
                self.shmem_currents[pos] = -1
            try:
                self.shmem_voltages[pos] = self.powersupplies[psu].getVoltage ()
            except TypeError:
                self.shmem_voltages[pos] = -1
            self.shmem_current_setpoints[pos] = -1

        # set up periodic database logging
        self.logger = logger.DataLogger (config, self.shmem_temperatures, self.shmem_currents, self.shmem_voltages)
        self.logger_timer = wx.Timer (self)
        self.Bind (wx.EVT_TIMER, self.updateDatabaseLogs, self.logger_timer)
        self.logger_timer.Start (5000)

        # set up information publishing via MQTT
        if config.getDatabase ('mqtt_broker'):
            self.mqtt_client = mqtt.Client (client_id = "ErYbLi-oven_control")
            self.mqtt_client.connect (config.getDatabase ('mqtt_broker'))
            self.mqtt_client.loop_start ()
            self.mqtt_topic_prefix = config.getDatabase ('mqtt_topic_prefix')
        else:
            self.mqtt_client = None

        # add a button for each configured oven
        self.button_oven = {}
        for oven in config.getOvenNames ():
            # control page
            self.button_oven[oven] = wx.ToggleButton (self.page_control, wx.ID_ANY, config.getOven (oven)['name'])
            self.button_oven[oven].Bind (wx.EVT_TOGGLEBUTTON, self.OnOvenBtnClick)
            self.sizer_horiz_oven_selection.Add (self.button_oven[oven], 1, wx.ALL|wx.EXPAND, 10)

        # automatic startup preparations
        self.check_list_box_oven_selection.SetItems (config.getOvenNames ())
        self.startup_timer = wx.Timer (self)
        self.Bind (wx.EVT_TIMER, self._startup_timer_callback, self.startup_timer)

        # populate temperature list
        column = self.list_ctrl_temperatures.GetColumn (1)
        column.SetAlign (wx.LIST_FORMAT_RIGHT)
        self.list_ctrl_temperatures.SetColumn (1, column)
        column = self.list_ctrl_temperatures.GetColumn (2)
        column.SetAlign (wx.LIST_FORMAT_RIGHT)
        self.list_ctrl_temperatures.SetColumn (2, column)

        for listpos, sensor in enumerate (config.getThermocoupleNames ()):
            self.list_ctrl_temperatures.InsertStringItem (listpos, sensor)

        # catch double clicks and enter on temperature list item
        self.list_ctrl_temperatures.Bind (wx.EVT_LIST_ITEM_ACTIVATED, self.OnTempListDoubleClick)

        matplotlib.rc ('xtick', labelsize = 8)
        matplotlib.rc ('ytick', labelsize = 8)

        # add temperature plot
        self.ydata_temperature = {}
        self.ydata_error = {}
        self.temp_figure = Figure (figsize = (3,1), constrained_layout = True)
        self.temp_axes = self.temp_figure.add_subplot (111)
        self.temp_canvas = FigureCanvas (self.page_monitor, -1, self.temp_figure)
        self.temp_axes.tick_params (direction = 'in', top = True, right = True)
        self.temp_axes.grid (axis = 'y', linewidth = 1)
        self.temp_axes.set_xmargin (0.)
        self.temp_axes.set_ylabel ("Is Temperature (C)", size = 8)
        self.temp_axes.xaxis.set_major_formatter (matplotlib.dates.DateFormatter ('%H:%M'))
        self.temp_canvas.mpl_connect ('button_release_event', self.OnTempPlotClicked)
        self.plot_error_signal = False

        self.temp_line = {}
        for listpos, sensor in enumerate (config.getThermocoupleNames ()):
            self.ydata_temperature[sensor] = []
            self.ydata_error[sensor] = []
            self.temp_line[sensor], = self.temp_axes.plot_date ([], [],
                    fmt = '-', tz = None, xdate = True, lw = 2)
            # set color in list to same as plot line color
            color = self.temp_line[sensor].get_color ()
            self.list_ctrl_temperatures.SetItemBackgroundColour (listpos, self._color_variant (color, 30))

        self.sizer_horiz_temp.Add (self.temp_canvas, 1, wx.ALL|wx.EXPAND, 3)

        # populate powersupply list
        column = self.list_ctrl_currents.GetColumn (1)
        column.SetAlign (wx.LIST_FORMAT_LEFT)
        column = self.list_ctrl_currents.GetColumn (2)
        column.SetAlign (wx.LIST_FORMAT_LEFT)

        for listpos, psu in enumerate (config.getPowersupplyNames ()):
            self.list_ctrl_currents.InsertStringItem (listpos, config.getPowersupply (psu)['name'])

        # catch double clicks and enter on powersupply list item
        self.list_ctrl_currents.Bind (wx.EVT_LIST_ITEM_ACTIVATED, self.OnPsuListDoubleClick)

        # add powersupply plot
        self.ydata_current = {}
        self.ydata_power = {}
        self.psu_figure = Figure (figsize = (3,1), constrained_layout = True)
        self.psu_axes = self.psu_figure.add_subplot (111)
        self.psu_canvas = FigureCanvas (self.page_monitor, -1, self.psu_figure)
        self.psu_axes.tick_params (direction = 'in', top = True, right = True)
        self.psu_axes.grid (axis = 'y', linewidth = 1)
        self.psu_axes.set_xmargin (0.)
        self.psu_axes.set_ylabel ("Is current (A)", size = 8)
        self.psu_axes.xaxis.set_major_formatter (matplotlib.dates.DateFormatter ('%H:%M'))
        self.psu_canvas.mpl_connect ('button_release_event', self.OnPSUPlotClicked)
        self.plot_power_signal = False

        self.psu_line = {}
        for listpos, psu in enumerate (config.getPowersupplyNames ()):
            self.ydata_current[psu] = []
            self.ydata_power[psu] = []
            self.psu_line[psu], = self.psu_axes.plot_date ([], [],
                    fmt = '-', tz = None, xdate = True, lw = 2)
            # set color in list to same as plot line color
            color = self.psu_line[psu].get_color ()
            self.list_ctrl_currents.SetItemBackgroundColour (listpos, self._color_variant (color,30))

        self.sizer_horiz_current.Add (self.psu_canvas, 1, wx.ALL|wx.EXPAND, 3)

        # populate heater setting combo box
        self.combo_box_heater_sel.SetItems (config.getHeaterNames ())
        self.combo_box_heater_sel.SetSelection (0)
        self.OnHeaterSelected (None)

        # set number of digits for PID parameters
        self.spin_ctrl_low_p.SetDigits (2)
        self.spin_ctrl_low_i.SetDigits (2)
        self.spin_ctrl_low_d.SetDigits (2)
        self.spin_ctrl_high_p.SetDigits (2)
        self.spin_ctrl_high_i.SetDigits (2)
        self.spin_ctrl_high_d.SetDigits (2)
        self.spin_ctrl_ramp_standard.SetDigits (1)
        self.spin_ctrl_ramp_emergency.SetDigits (1)
        self.spin_ctrl_low_p.SetIncrement (0.1)
        self.spin_ctrl_low_i.SetIncrement (0.01)
        self.spin_ctrl_low_d.SetIncrement (0.01)
        self.spin_ctrl_high_p.SetIncrement (0.1)
        self.spin_ctrl_high_i.SetIncrement (0.01)
        self.spin_ctrl_high_d.SetIncrement (0.01)

        # populate e-mail recipients list
        self.populateRecipients ()

        # fill in actual values in general settings section
        self.spin_ctrl_plot_update_interval.SetValue (
                    float (config.getGeneral ('plot_update_interval'))
                )
        self.spin_ctrl_plots_max_points.SetValue (
                    float (config.getGeneral ('plot_max_points'))
                )
        self.spin_ctrl_off_state_temp.SetValue (
                    float (config.getGeneral ('off_state_temperature'))
                )
        if config.getDatabase ('logging_enabled') == 'True':
            self.combo_box_db_logging.SetSelection (0)
        else:
            self.combo_box_db_logging.SetSelection (1)

        # select today in calendar widget and set periodic update every 30 minutes
        self._calendar_update_lowerdate ()
        self.calendar_update_timer = wx.Timer (self)
        self.Bind (wx.EVT_TIMER, self._calendar_update_lowerdate, self.calendar_update_timer)
        self.calendar_update_timer.Start (30 * 60 * 1000)

        ### mostly finished setting up the GUI ###

        # start thermocouple and powersupply updater processes
        self.thermocouple_process = multiprocessing.Process (
                target = thermocouple_process.thermocouple_process,
                args = (self.thermocouples,
                        float (config.getGeneral ('thermocouple_polling_interval')),
                        int (config.getGeneral ('thermocouple_averaging')),
                        self.shmem_temperatures,
                        self.queue_temperatures
                       )
               )
        self.thermocouple_process.start ()

        self.powersupply_process = multiprocessing.Process (
                target = powersupply_process.powersupply_process,
                args = (self.powersupplies,
                        float (config.getGeneral ('powersupply_polling_interval')),
                        self.shmem_currents,
                        self.shmem_voltages,
                        self.shmem_current_setpoints,
                        self.queue_powersupplies
                       )
               )
        self.powersupply_process.start ()

        # Update the status area in periodic intervals
        self.status_timer = wx.Timer (self)
        self.Bind (wx.EVT_TIMER, self._status_timer_callback, self.status_timer)
        self.status_timer.Start (1000)

        # PID thread initialization
        self.queue_PIDs = multiprocessing.Queue ()
        self.PIDthread = pidthread.PIDthread (
                self.shmem_temperatures,
                self.shmem_current_setpoints,
                self.shmem_currents,
                config,
                self.queue_PIDs
                )
        self.PIDthread.start ()

        # refresh temperature and powersupply list and plots, and set timer
        self._updateTempAndPowersupply ()
        self.timer_temp_and_psu = wx.Timer (self)
        self.Bind (wx.EVT_TIMER, self._updateTempAndPowersupply, self.timer_temp_and_psu)
        self.timer_temp_and_psu.Start (
                1000 * float (config.getGeneral ('list_update_interval'))
                )

        # Events
        self.Bind (wx.EVT_CLOSE, self.OnExit)

        # Done
        self.SetOvenStatusText  ("Idle...")
        self.SetTimedStatusText ("Startup done", 3)
        self.MqttPublish ("state", "idle", True)

    """General functions"""

    def SetTimedStatusText (self, text, timeout = None):
        """Set a statusbar message that is cleared after <timeout> sec"""
        self.SetStatusText (text)
        if timeout != None:
            self.timer = wx.Timer (self)
            self.Bind (wx.EVT_TIMER, self.ClearStatusText, self.timer)
            self.timer.Start (timeout * 1000, oneShot = True)

    def ClearStatusText (self, e):
        """Clear the status text in the 1st (left) status bar field"""
        self.SetStatusText ("")

    def SetOvenStatusText (self, text):
        """Set the status text in the 2nd (right) statusbar field"""
        self.SetStatusText (text, 1);

    def MqttPublish (self, topic, payload, retain = False):
        """Publish oven status information to an MQTT broker.
        It payload is a dictionary the data will be transmitted in JSON form."""
        if not self.mqtt_client:
            return

        try:
            (rc, mid) = self.mqtt_client.publish (
                    topic = "{}/{}".format (self.mqtt_topic_prefix, topic),
                    payload = json.dumps (payload),
                    qos = 1,
                    retain = retain
                )
            if rc != mqtt.MQTT_ERR_SUCCESS:
                # error while trying to publish
                # just in case try to reconnect to the MQTT broker
                # and pusblish the message again
                self.mqtt_client.reconnect ()
                self.mqtt_client.publish (
                        topic = "{}/{}".format (self.mqtt_topic_prefix, topic),
                        payload = json.dumps (payload),
                        qos = 1,
                        retain = retain
                    )
        except:
            pass

    def OnExit (self, e):
        """Exit application with proper cleanup"""
        dlg = wx.MessageDialog (self,
                " Do you really want to close \n the YbErLi-oven control program?",
                "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal ()
        dlg.Destroy ()
        self.buzzer.AcknowledgeBeepShort ()
        if result == wx.ID_OK:
            self.SetTimedStatusText ("Wating for processes to shut down")
            self.MqttPublish ("state", "program exited", True)
            # signal all child processes and threads to quit
            self.queue_PIDs.put ('q')
            self.queue_temperatures.put ('q')
            self.queue_powersupplies.put ('q')
            self.PIDthread.join ()
            self.thermocouple_process.join ()
            self.powersupply_process.join ()
            # close GUI
            self.Destroy ()

    def _color_variant (self, hex_color, brightness_offset = 1):
	"""Take a color like #87c95f and produces a lighter or darker variant
	Taken from https://chase-seibert.github.io/blog/2011/07/29/python-calculate-lighterdarker-rgb-colors.html
	"""
	if len (hex_color) != 7:
            raise Exception ("Passed %s into color_variant(), needs to be in #87c95f format." % hex_color)
	rgb_hex = [hex_color[x:x+2] for x in [1, 3, 5]]
	new_rgb_int = [int (hex_value, 16) + brightness_offset for hex_value in rgb_hex]
	new_rgb_int = [min ([255, max ([0, i])]) for i in new_rgb_int] # make sure new values are between 0 and 255
	# hex() produces "0x88", we want just "88"
	return "#" + "".join([hex(i)[2:] for i in new_rgb_int])

    """Functions of the oven control page"""

    def OnOvenBtnClick (self, evt):
        """Activate oven buttons"""
        button = evt.GetEventObject ()
        self.buzzer.AcknowledgeBeepShort ()

        if self.oven_status not in ['is off', 'is low', 'idle']:
            button.SetValue (not button.GetValue ())
            dlg = wx.MessageDialog (self,
                                    "Cannot change the oven selection.\n\n"
                                    "This is only possible if the oven is\n"
                                    "in Off, Low or Idle state.", "Information",
                                    wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal ()
            dlg.Destroy ()
            self.buzzer.AcknowledgeBeepShort ()
            return

        if button.GetValue ():
            button.SetBackgroundColour ((150, 255, 150))
        else:
            button.SetBackgroundColour (wx.NullColour)

    def OnHighClicked (self, evt = None, automatic = False):
        """Start ramp up of selected ovens"""
        selected = self._getSelectedOvens ()
        self.buzzer.AcknowledgeBeepShort ()

        # Confirm that interlock is fine
        if self._interlockCheckBeforeRamp ():
            self.button_ramp_high.SetValue (False)
            return

        # Confirm that some oven is selected
        if len (selected) == 0:
            dlg = wx.MessageDialog (self,
                                    "Please select oven(s) for heating first.", "Information",
                                    wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal ()
            dlg.Destroy ()
            self.buzzer.AcknowledgeBeepShort ()
            self.button_ramp_high.SetValue (False)
            return True

        # Oven is already hot
        if not automatic and self.oven_status.endswith (' high'):
            if self._confirmFreeze () == wx.ID_OK:
                # stop ramp and freeze powersupplies
                self._stopRampAndFreezePowersupplies (selected)
            else:
                self.SetTimedStatusText ("Heating not interrupted", 3)
            # Do not execute remaining function
            return True

        # Confirm that the user really wants to start heating
        if not automatic and self._confirmStartRamp ("HEATING") != wx.ID_OK:
            self.SetTimedStatusText ("Heating not started", 3)
            self.button_ramp_high.SetValue (False)
            return True

        self.interlock_is_critical = True

        # First set all ovens that are not selected to go to low temperature ...
        not_selected = list (set (config.getOvenNames ()) - set (selected))
        if len (not_selected) > 0:
            self._updateHeaterSetpoints (not_selected, 'a', 'temp_low')

        # ... then set everything selected to ramp to high
        self._updateHeaterSetpoints (selected, 'a', 'temp_high')

        self.totalramptime = self._calculate_ramp_time ()
        self.gauge_oven_ramp.SetValue (0)
        self.oven_status = 'ramp to high'

        for button in self.oven_buttonlist:
            if button != self.button_ramp_high:
                    button.SetValue (False)
            button.SetBackgroundColour (wx.NullColour)
        self.button_ramp_high.SetBackgroundColour ((255, 255, 150))
        self.SetTimedStatusText ("Ramp to High started", 3)
        self.SetOvenStatusText ("Ramping to High...")
        self.MqttPublish ("state", "ramp to high", True)

    def OnLowClicked (self, evt = None, automatic = False):
        """Start ramp down of all ovens"""
        # Get all ovens as selected for this target
        selected = config.getOvenNames ()
        self.buzzer.AcknowledgeBeepShort ()

        # Confirm that interlock is fine
        if self._interlockCheckBeforeRamp ():
            self.button_ramp_low.SetValue (False)
            return

        # Oven is already low
        if not automatic and self.oven_status.endswith (' low'):
            if self._confirmFreeze () == wx.ID_OK:
                # stop ramp and freeze powersupplies
                self._stopRampAndFreezePowersupplies (selected)
            else:
                self.SetTimedStatusText ("Cooling not interrupted", 3)
            # Do not execute remaining function
            return True

        # Confirm that the user really wants to start cooling
        if not automatic and self._confirmStartRamp ("COOLING") != wx.ID_OK:
            self.button_ramp_low.SetValue (False)
            self.SetTimedStatusText ("Cooling not started", 3)
            return True

        self.interlock_is_critical = True

        self._updateHeaterSetpoints (selected, 'a', 'temp_low')

        self.totalramptime = self._calculate_ramp_time ()
        self.gauge_oven_ramp.SetValue (0)
        self.oven_status = 'ramp to low'

        for button in self.oven_buttonlist:
            if button != self.button_ramp_low:
                    button.SetValue (False)
            button.SetBackgroundColour (wx.NullColour)
        self.button_ramp_low.SetBackgroundColour ((255, 255, 150))
        self.SetTimedStatusText ("Ramp to Low started", 3)
        self.SetOvenStatusText ("Ramping to Low...")
        self.MqttPublish ("state", "ramp to low", True)

    def OnOffClicked (self, evt = None, automatic = False):
        """Start ramp to off of all ovens"""
        # Get all ovens as selected for this target
        selected = config.getOvenNames ()
        self.buzzer.AcknowledgeBeepShort (3)

        # Oven already ramps to off
        if not automatic and self.oven_status == "ramp to off":
            if self._confirmFreeze () == wx.ID_OK:
                # stop ramp and freeze powersupplies
                self._stopRampAndFreezePowersupplies (selected)
                return True

        # Oven is already in off or emergency-off
        if not automatic and self.oven_status.startswith ('is') and self.oven_status.endswith ('off'):
            dlg = wx.MessageDialog (self,
                    "Oven and powersupplies are already in an off state.\n"\
                    "There is nothing more to be done.",
                    "Oven notice", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal ()
            dlg.Destroy ()
            self.buzzer.AcknowledgeBeepShort ()
            # Do not execute remaining function
            return True

        # The oven was not already off, so better check the interlock
        if self._interlockCheckBeforeRamp ():
            self.button_ramp_off.SetValue (False)
            return

        # Confirm that the user really wants to start cooling
        if not automatic and self._confirmStartRamp ("TURNING OFF") != wx.ID_OK:
            self.button_ramp_off.SetValue (False)
            self.SetTimedStatusText ("Cooling to off not started", 3)
            return True

        self.interlock_is_critical = True

        self._updateHeaterSetpoints (selected, 'a', 'temp_off')

        self.totalramptime = self._calculate_ramp_time ()
        if self.totalramptime == 0:
            self.button_ramp_off.SetValue (False)
            dlg = wx.MessageDialog (self,
                    "Oven is already at or below the off-state temperature.\n"\
                    "There is nothing more to be done.",
                    "Oven notice", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal ()
            dlg.Destroy ()
            return True
        self.gauge_oven_ramp.SetValue (0)
        self.oven_status = 'ramp to off'

        for button in self.oven_buttonlist:
            if button != self.button_ramp_high:
                    button.SetValue (False)
            button.SetBackgroundColour (wx.NullColour)
        self.button_ramp_off.SetBackgroundColour ((255, 255, 150))
        self.SetTimedStatusText ("Ramp to Off started", 3)
        self.SetOvenStatusText ("Ramping to Off...")
        self.MqttPublish ("state", "ramp to off", True)

    def OnEmergencyClicked (self, evt):
        """Start fast emergency ramp to off of all ovens"""
        # Get all ovens as selected for this target
        selected = config.getOvenNames ()
        self.buzzer.AcknowledgeBeepShort (3)

        # Oven already ramps to off
        if self.oven_status == "ramp to emergency-off":
            if self._confirmFreeze () == wx.ID_OK:
                # stop ramp and freeze powersupplies
                self._stopRampAndFreezePowersupplies (selected)
                return True

        # Oven is already in off or emergency-off
        if self.oven_status.startswith ('is') and self.oven_status.endswith ('off'):
            dlg = wx.MessageDialog (self,
                    "Oven and powersupplies are already in an off state.\n"\
                    "There is nothing more to be done.",
                    "Oven notice", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal ()
            dlg.Destroy ()
            self.buzzer.AcknowledgeBeepShort ()
            # Do not execute remaining function
            return True

        # Confirm that the user really wants to start cooling
        if self._confirmStartRamp ("EMERGENCY COOLING") != wx.ID_OK:
            self.button_ramp_emergency.SetValue (False)
            self.SetTimedStatusText ("Emergency cooling not started", 3)
            return True

        # The whole point of the emergency ramp is to bring the oven down in
        # case something goes wrong. So disable the interlock.
        self.interlock_is_critical = False

        self._updateHeaterSetpoints (selected, 'e', 'temp_off')

        self.totalramptime = self._calculate_ramp_time ()
        if self.totalramptime == 0:
            self.button_ramp_off.SetValue (False)
            dlg = wx.MessageDialog (self,
                    "Oven is already at or below the off-state temperature.\n"\
                    "There is nothing more to be done.",
                    "Oven notice", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal ()
            dlg.Destroy ()
            return True
        self.gauge_oven_ramp.SetValue (0)
        self.oven_status = 'ramp to emergency-off'

        for button in self.oven_buttonlist:
            if button != self.button_ramp_high:
                    button.SetValue (False)
            button.SetBackgroundColour (wx.NullColour)
        self.button_ramp_emergency.SetBackgroundColour ((255, 150, 150))
        self.SetTimedStatusText ("Emergency ramp to Off started", 3)
        self.SetOvenStatusText ("Emergency ramping to Off...")
        self.MqttPublish ("state", "emergency ramp to off", True)

    def OnInterlockDClicked (self, evt):
        """Disable/Enable individual interlocks"""
        statictext = evt.GetEventObject ()

        labellist = (
                ("CHILLER", self.label_interlock_water, interlock.Interlock.WATER_FAIL),
                ("TEMPERATURE", self.label_interlock_temp, interlock.Interlock.TEMP_FAIL),
                ("HEATER", self.label_interlock_heater, interlock.Interlock.HEATER_FAIL),
                ("POWER SUPPLY", self.label_interlock_powersupply, interlock.Interlock.PSU_FAIL),
                ("UPS", self.label_interlock_ups, interlock.Interlock.UPS_FAIL)
            )
        for (name, label, bitmask) in labellist:
            if statictext == label:
                # found label that was clicked
                if not self.interlock_ignore_mask & bitmask:
                    # interlock is currently enabled -> ask for confirmation before disable
                    self.buzzer.AcknowledgeBeepShort ()
                    if self._confirmDisableInterlock (name) == wx.ID_OK:
                        self.interlock_ignore_mask ^= bitmask
                        self.buzzer.AcknowledgeBeepShort (3)
                else:
                    # interlock is currently disabled -> enable without confirmation check
                    self.interlock_ignore_mask ^= bitmask
                    self.buzzer.AcknowledgeBeepShort (2)

        # force full update of interlock status
        # (this will also give the label the proper background color)
        self.interlock_oldstatus = -1
        self._update_interlock ()

    def _confirmDisableInterlock (self, name):
        """Confirmation dialog before disabling an interlock

        :param name: name string of interlock to be disabled
        :return: return value of MessageDialog, is wx.ID_OK if user confirms
        """

        dlg = wx.MessageDialog (self,
                 "You are about to disable the {}\n"
                 "interlock. Please confirm to proceed.".format (name),
                 "Confirmation", 
                 wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
        result = dlg.ShowModal ()
        dlg.Destroy ()
        return result

    def _getSelectedOvens (self):
        """Determine currently selected ovens

        :return: list of selected oven names
        """
        selected = []
        for oven in config.getOvenNames ():
            if self.button_oven[oven].GetValue ():
                selected.append (oven)

        return selected

    def _confirmFreeze (self):
        """Confirmation dialog to interrupt ramp to to freeze ovens

        :return: return value of MessageDialog, is wx.ID_OK if user confirms
        """
        if self.oven_status.startswith ('ramp '):
            dlg = wx.MessageDialog (self,
                    "This target is currently running.\n\n"
                    "Do you want to interrupt the ramp and freeze\n"
                    "the powersupplies at their current settings?",
                    "Confirmation", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        else:
            dlg = wx.MessageDialog (self,
                    "This target is currently active.\n\n"
                    "Do you want to interrupt active temperature\n"
                    "stabilization and freeze the powersupplies\n"
                    "at their current settings?",
                    "Confirmation", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal ()
        dlg.Destroy ()
        self.buzzer.AcknowledgeBeepShort ()
        return result

    def _stopRampAndFreezePowersupplies (self, selected):
        """Stop an ongoing ramp and freeze the powersupply output at its current value.

        :param selected: List of powersupply names to be frozen
        """
        self._updateHeaterSetpoints (selected, 'f', 'current')
        self.totalramptime = self._calculate_ramp_time ()
        self.gauge_oven_ramp.SetValue (0)
        self.oven_status = 'idle'

        for button in self.oven_buttonlist:
            button.SetBackgroundColour (wx.NullColour)
            button.SetValue (False)

        self.SetTimedStatusText ("Temperature ramp interrupted on user request", 3)
        self.SetOvenStatusText ("Idle...")
        self.MqttPublish ("state", "idle", True)

    def _confirmStartRamp (self, action):
        """Confirmation dialog at start of oven ramp

        :param action: string of action to do, e.g. "HEATING"
        :return: return value of MessageDialog, is wx.ID_OK if user confirms
        """
        dlg = wx.MessageDialog (self,
                "Do you really want to start\n{} the oven?".format (action),
                "Confirmation", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal ()
        dlg.Destroy ()
        self.buzzer.AcknowledgeBeepShort ()
        return result

    def _interlockCheckBeforeRamp (self):
        """Make sure that the interlock all green before bringing up the
        powersupplies from the off status

        :return: True on interlock failure, False if everything is OK
        """

        # get "effective" interlock status by considering also masked interlocks
        effective_interlock_status = self.interlock.status & ~self.interlock_ignore_mask

        if effective_interlock_status == interlock.Interlock.ALL_OK:
            return False

        dlg = wx.MessageDialog (self,
                "Interlock failure status.\n\n"\
                "Cannot start oven ramp as interlock is not\n"
                "all green. Interlock failure details:\n{}".format (self.interlock.details),
                "Interlock notice", wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal ()
        dlg.Destroy ()
        self.buzzer.AcknowledgeBeepShort ()

        return True

    def _updateHeaterSetpoints (self, ovens, state, target):
        """Helper function for clicked oven button to update heater objects.
        Update the target temperatures, set the temperature setpoint to the
        current temperature and turn on the powersupply.

        :param ovens: list of oven names to be updated (will do all their heaters)
        :param state: state of heater, i.e. 'a'ctive, 'e'mergency, 'o'ff or 'f'reeze
        :param target: name of temperature target,
                       i.e. 'temp_high', 'temp_low', 'temp_off' or 'current'
        """
        for oven in ovens:
            for heatername in config.getOven (oven)['heaters']:
                self.PIDthread.heaters[heatername].state = state

                # current temperature of the heater's thermocouple for later use
                is_temperature = self.shmem_temperatures[
                            self.thermocouples[
                                self.PIDthread.heaters[heatername].info['thermocouple']
                            ].position
                        ]

                if state == 'f':
                    # setting output to -1 will cause the PID to be reset on the next start
                    self.PIDthread.PIDs[heatername].output = -1
                if target == 'temp_high' or target == 'temp_low':
                    self.PIDthread.heaters[heatername].target = self.PIDthread.heaters[heatername].info[target]
                elif target == 'temp_off':
                    off_temperature = float (config.getGeneral ('off_state_temperature'))
                    # only set off state temperature if current temperature is actually higher
                    if off_temperature < is_temperature:
                        self.PIDthread.heaters[heatername].target = off_temperature
                    else:
                        self.PIDthread.heaters[heatername].target = is_temperature
                else: # must be 'current' by now, the special target for a freeze operation
                    self.PIDthread.heaters[heatername].target = is_temperature

                if state != 'f':
                    # start with the present temperature as setpoint
                    self.PIDthread.heaters[heatername].setpoint = is_temperature
                else:
                    # for a frozen target there is no setpoint temperature
                    self.PIDthread.heaters[heatername].setpoint = -1

                self.PIDthread.PIDstability[heatername]['startup_check'] = False
                if target != "temp_off" and state != "f":
                    # check for a "cold start", that is, if we are at very low temperatures
                    # we will make the PID less agressive and reduce the ramping speed in
                    # pidthread.py to prevent catastrohpic overshoots. Once we are then out
                    # off this startup mode the PID thread will reset the flag to False.
                    self.PIDthread.PIDstability[heatername]['startup_check'] = True

                # Notify powersupply thread to turn on powersupply output
                self.queue_powersupplies.put ('on ' + self.PIDthread.heaters[heatername].info['powersupply'])

        # notify the PID thread in case we are ramping to off
        if target == 'temp_off':
            self.PIDthread.ramp_to_off = True
        else:
            self.PIDthread.ramp_to_off = False

        # special addition: if a ramp has started disable temperature smoothing
        self.queue_temperatures.put (1) # smoothing factor 1 equals no smoothing

    def _calculate_ramp_time (self):
        """Estimate how much time the remaining ramp will take"""
        heaters = self.PIDthread.heaters
        longest = 0
        remaining = 0
        for heater in heaters.values ():
            # Calculate the remaining time for this oven
            if heater.state == 'a':
                remaining = abs ((heater.target - heater.setpoint) / (heater.info['ramp_speed']/60.))
            if heater.state == 'e':
                remaining = abs ((heater.target - heater.setpoint) / (heater.info['emergency_ramp_speed']/60.))
            if remaining > longest:
                longest = remaining
            remaining = 0

        return longest

    def _status_timer_callback (self, e):
        """Update oven ramp and interlock statuses"""

        self._update_interlock ()

        time_remaining = self._calculate_ramp_time ()
        fraction = 1.
        if self.totalramptime > 0:
            fraction = max(0, min (1, (self.totalramptime - time_remaining) / self.totalramptime))
            if time_remaining < 1:
                fraction = 1.
            self.gauge_oven_ramp.SetValue (100. * fraction)

        if time_remaining > 0:
            # update with remaining time information
            minutes, seconds = divmod (time_remaining, 60)
            hours, minutes = divmod (minutes, 60)
            time_string = "%02d:%02d:%02d" % (hours, minutes, seconds)
            self.label_oven_status.SetLabel ("Remaining time for ramp: " + time_string)
            self.MqttPublish ("ramp_status", {"ETA": time_string, "fraction": round (fraction, 4)})
        elif self.label_oven_status.GetLabel().startswith ("Remaining "):
            # a ramp just finished
            self.queue_temperatures.put (1) # enable temperature smoothing (OK, not really for now)
            if self.oven_status == 'ramp to high':
                self.label_oven_status.SetLabel ("Oven is in HOT state")
                self.button_ramp_high.SetBackgroundColour ((150, 255, 150))
                self.SetTimedStatusText ("Ramp to High finished", 3)
                self.SetOvenStatusText ("Oven is HOT")
                self.MqttPublish ("state", "oven is hot", True)
                self.oven_status = 'is high'
                self.interlock_is_critical = True
                self.sendMailRampFinished ()
                self.buzzer.AcknowledgeBeepLong ()
            if self.oven_status == 'ramp to low':
                self.label_oven_status.SetLabel ("Oven is in LOW state")
                self.button_ramp_low.SetBackgroundColour ((150, 255, 150))
                self.SetTimedStatusText ("Ramp to Low finished", 3)
                self.SetOvenStatusText ("Oven is LOW")
                self.MqttPublish ("state", "oven is low", True)
                self.oven_status = 'is low'
                self.interlock_is_critical = True
                self.sendMailRampFinished ()
                self.buzzer.AcknowledgeBeepLong ()
            if self.oven_status == 'ramp to off' or \
               self.oven_status == 'ramp to emergency-off':
                self.label_oven_status.SetLabel ("Oven is in OFF state")
                if self.oven_status == 'ramp to off':
                    self.button_ramp_off.SetBackgroundColour ((150, 255, 150))
                else:
                    self.button_ramp_emergency.SetBackgroundColour ((150, 255, 150))
                self.SetTimedStatusText ("Ramp to Off finished", 3)
                self.SetOvenStatusText ("Oven is OFF")
                self.MqttPublish ("state", "oven is off", True)
                # put all powersupply currents to -1
                # this puts the acutal set current to 0 A and shows as "----" in the list
                for psu in self.powersupplies:
                    pos = self.powersupplies[psu].position
                    self.shmem_current_setpoints[pos] = -1
                for heater in self.PIDthread.heaters.values ():
                    # turn off PIDs for heater
                    heater.state = 'o'
                    # indicate that there is no temperature setpoint
                    heater.setpoint = -1
                    # disable powersupply output (processed by powersupply_process)
                    self.queue_powersupplies.put ('off ' + heater.info['powersupply'])
                self.oven_status = 'is off'
                self.PIDthread.ramp_to_off = False
                self.interlock_is_critical = False
                self.sendMailRampFinished ()
                self.buzzer.AcknowledgeBeepLong ()
            if self.oven_status == 'idle':
                self.label_oven_status.SetLabel ("Oven is idle")

        self.label_oven_status.GetParent().Layout ()

    def _update_interlock (self):
        """Update status of the various interlock systems"""

        self.interlock.update ()

        # get "effective" interlock status by considering also masked interlocks
        effective_interlock_status = self.interlock.status & ~self.interlock_ignore_mask

        if effective_interlock_status == self.interlock_oldstatus:
            # interlock status unchanged
            if (self.interlock_is_critical == self.interlock_is_critical_oldstate) \
                    and (effective_interlock_status != interlock.Interlock.ALL_OK):
                # No change in the interlock criticality either, so no need to continue.
                # However, skip the rest only if the interlock fails as otherwise the
                # interlock has come back to good condition and we need to update the
                # interlock indicators to green.
                return

        self.interlock_is_critical_oldstate = self.interlock_is_critical

        # prepare interlock summary for MQTT publishing
        interlock_summary = {
                "cooling": "ok",
                "temperature": "ok",
                "heater": "ok",
                "powersupplies": "ok",
                "ups": "ok",
                "overall": "ok"
            }
        if self.interlock_ignore_mask & interlock.Interlock.WATER_FAIL:
            interlock_summary['cooling'] = "disabled"
        if self.interlock_ignore_mask & interlock.Interlock.TEMP_FAIL:
            interlock_summary['temperature'] = "disabled"
        if self.interlock_ignore_mask & interlock.Interlock.HEATER_FAIL:
            interlock_summary['heater'] = "disabled"
        if self.interlock_ignore_mask & interlock.Interlock.PSU_FAIL:
            interlock_summary['powersupplies'] = "disabled"
        if self.interlock_ignore_mask & interlock.Interlock.UPS_FAIL:
            interlock_summary['ups'] = "disabled"

        if self.interlock_is_critical:
            signal_color = (255, 0, 0)
        else:
            # interlock messages become warnings
            signal_color = (255, 190, 0)

        # update status label colors and MQTT status
        labellist = (
                ("cooling", self.label_interlock_water, interlock.Interlock.WATER_FAIL),
                ("temperature", self.label_interlock_temp, interlock.Interlock.TEMP_FAIL),
                ("heater", self.label_interlock_heater, interlock.Interlock.HEATER_FAIL),
                ("powersupplies", self.label_interlock_powersupply, interlock.Interlock.PSU_FAIL),
                ("ups", self.label_interlock_ups, interlock.Interlock.UPS_FAIL)
            )
        for (name, label, bitmask) in labellist:
            if effective_interlock_status & bitmask:
                # interlock failed
                label.SetBackgroundColour (signal_color)
                interlock_summary[name] = "fail"
            else:
                # interlock disabled or OK
                if self.interlock_ignore_mask & bitmask:
                    label.SetBackgroundColour ((128, 128, 128))
                else:
                    label.SetBackgroundColour ((0, 255, 0))

        # publish interlock state via MQTT
        if effective_interlock_status != self.interlock_oldstatus:
            if effective_interlock_status and self.interlock_is_critical:
                interlock_summary['overall'] = "fail"
            self.MqttPublish ("interlock", interlock_summary, True)

        if not self.interlock_is_critical:
            # if the oven is off do not take any further action
            return

        # react to power supply failure by freezing the system
        if effective_interlock_status & interlock.Interlock.PSU_FAIL:
            self._stopRampAndFreezePowersupplies (config.getOvenNames ())
            self.SetTimedStatusText ("System frozen due to powersupply failure", 30)
            self.label_oven_status.SetLabel ("Oven is idle")
            self.label_oven_status.GetParent().Layout ()
            self._interlockDialog (self.interlock.details)

        # react to temperature failure
        if effective_interlock_status & interlock.Interlock.TEMP_FAIL:
            sensorfail = False
            for temp in self.shmem_temperatures:
                if temp < 0:
                    sensorfail = True
            if sensorfail:
                # freeze system is a sensor fails
                self._stopRampAndFreezePowersupplies (config.getOvenNames ())
                self.SetTimedStatusText ("System frozen due to thermocouple failure", 30)
                self.label_oven_status.SetLabel ("Oven is idle")
                self.label_oven_status.GetParent().Layout ()
                self._interlockDialog (self.interlock.details)
            else:
                # emergency ramp down on temperature over maximum
                self._updateHeaterSetpoints (config.getOvenNames (), 'e', 'temp_off')
                self.totalramptime = self._calculate_ramp_time ()
                self.gauge_oven_ramp.SetValue (0)
                self.oven_status = 'ramp to emergency-off'
                for button in self.oven_buttonlist:
                    button.SetBackgroundColour (wx.NullColour)
                self.button_ramp_emergency.SetBackgroundColour ((255, 150, 150))
                self.SetTimedStatusText ("Automatic emergency ramp to Off started", 30)
                self.SetOvenStatusText ("Emergency ramping to Off...")
                self.MqttPublish ("state", "emergency ramp to off", True)
                self._interlockDialog (self.interlock.details)

        # react to cooling, heater or UPS failure with emergency shutdown
        if (effective_interlock_status & interlock.Interlock.WATER_FAIL) or\
           (effective_interlock_status & interlock.Interlock.HEATER_FAIL) or\
           (effective_interlock_status & interlock.Interlock.UPS_FAIL):
            self._updateHeaterSetpoints (config.getOvenNames (), 'e', 'temp_off')
            self.totalramptime = self._calculate_ramp_time ()
            self.gauge_oven_ramp.SetValue (0)
            self.oven_status = 'ramp to emergency-off'
            for button in self.oven_buttonlist:
                button.SetBackgroundColour (wx.NullColour)
            self.button_ramp_emergency.SetBackgroundColour ((255, 150, 150))
            self.SetTimedStatusText ("Automatic emergency ramp to Off started", 30)
            self.SetOvenStatusText ("Emergency ramping to Off...")
            self.MqttPublish ("state", "emergency ramp to off", True)
            self._interlockDialog (self.interlock.details)

        if effective_interlock_status == interlock.Interlock.ALL_OK and \
           effective_interlock_status != self.interlock_oldstatus:
            self.SetTimedStatusText ("All interlocks have come back to OK again", 30)

        self.interlock_oldstatus = effective_interlock_status

        return None

    def _interlockDialog (self, msg):
        """Notify the user about the emergency at hand via dialog and mail
        and do the beeping.

        :param msg: message string to be displayed
        """

        self.beeper_timer = wx.Timer (self)
        self.Bind (wx.EVT_TIMER, self._SOSbeeper, self.beeper_timer)
        self.beeper_timer.Start (3000)

        # Send an error e-mail
        recipients = config.getRecipients ()
        if len (recipients) > 0:
            subject = "[ErYbLi-oven] Oven interlock FAILURE"
            body = "Dear ErYbLi experiment user,\n\n"\
                   "This is the ErYbLi-oven control program.\n"\
                   "I have just detected an interlock failure.\n"\
                   "The known details on the cause of the failure are:\n\n{}\n\n"\
                   "As additional information here is the last data of the thermocouples:\n".format (msg)

            padding = max (len (x) for x in config.getThermocoupleNames ())
            for pos,tc in enumerate (config.getThermocoupleNames ()):
                body = body + "{:{width}}: {:7.2f} deg C\n".format (tc, self.shmem_temperatures[pos], width=padding)

            body = body + "\nAlso, some information on the powersupply currents:\n"

            padding = max (len (x) for x in config.getPowersupplyNames ())
            for pos,psu in enumerate (config.getPowersupplyNames ()):
                body = body + "{:{width}}: {:5.2f} A\n".format (psu, self.shmem_currents[pos], width=padding)

            body = body + "\nPlease help me in fixing the situation.\n\n"\
                    "Yours,\nthe ErYbLi-oven control program"
            try:
                server = config.getGeneral ('smtp_server')
                if server:
                    ms = mailsystem.MailSystem (recipients, server)
                    ms.sendMessage (subject, body)
            except:
                pass

        # Show a notice on screen
        dlg = wx.MessageDialog (self,
                "Interlock FAILURE detection.\n\n"\
                "Details on cause of failure:\n{}".format (msg),
                "Interlock notice", wx.OK|wx.ICON_EXCLAMATION)
        dlg.SetOKLabel ("&Dismiss and Silence alarm")
        dlg.ShowModal ()
        dlg.Destroy ()
        self.buzzer.AcknowledgeBeepShort ()

        self.beeper_timer.Stop ()

    def _SOSbeeper (self, e = None):
        """Callback function to do the SOS beeping"""

        self.buzzer.MorseSend ("SOS")

    def sendMailRampFinished (self):
        """Send an email message to all recipients that the oven ramp is done."""

        recipients = config.getRecipients ()
        if len (recipients) == 0:
            return

        if self.oven_status == "is high":
            action = "startup"
        elif self.oven_status == "is low":
            action = "shutdown"
        else:
            action = "shutdown to OFF"

        subject = "[ErYbLi-oven] Oven {} complete".format (action)

        body = "Dear ErYbLi experiment user,\n\n"\
               "This is the ErYbLi-oven control program.\n"\
               "I am pleased to announce that the oven {} is complete.\n\n".format (action)
        if self.oven_status == "is high":
            body = body + "I wish you, also today, a successful experiment.\n\n"
        else:
            body = body + "Thanks, as always, for your hard work.\n\n"
        body = body + "Yours,\nthe ErYbLi-oven control program"

        try:
            server = config.getGeneral ('smtp_server')
            if server:
                ms = mailsystem.MailSystem (recipients, server)
                ms.sendMessage (subject, body)
        except:
            dlg = wx.MessageDialog (self,
                    "Could not send notification e-mails.\n"
                    "Please check your settings and internet connectivity.",
                    "Messaging notice", wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal ()
            dlg.Destroy ()
            self.buzzer.AcknowledgeBeepShort ()

    def updateDatabaseLogs (self, e = None):
        """Wrapper function to write current value to database and to report back errors"""
        if config.getDatabase ('logging_enabled') == 'False':
            # logging disabled for now by user settings
            return

        retval = self.logger.updateLogs ()

        # Logging sometimes fails with a MySQL connection timeout. I suspect
        # that is due to the Raspberry being too busy with something else.
        # Anyway, we give the logger a second chance before finally failing
        # with a message if it should fail again.
        if retval != True:
            retval = self.logger.updateLogs ()

        if retval != True:
            self.buzzer.MorseSend ("SQL")
            dlg = wx.MessageDialog (self,
                    "Error when inserting values into database:\n{}".format (retval),
                    "Database error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal ()
            dlg.Destroy ()
            self.buzzer.AcknowledgeBeepShort ()

    """Functions of the oven monitor page"""

    def _updateTempAndPowersupply (self, e = None):
        """Helper callback function to update both reports sequentially"""
        self.updateTempInfo ()
        self.updatePowersupplyInfo ()

    def updateTempInfo (self, e = None):
        """Update the temperature list and plot with latest values"""

        now = matplotlib.dates.date2num (datetime.now ())
        mqtt_temperature_dict = {}
        plot_changed = False

        for pos, sensor in enumerate (config.getThermocoupleNames ()):

            # find heater corresponding to the current thermocouple
            temp_set = None
            for heatername in config.getHeaterNames ():
                if config.getHeater (heatername)['thermocouple'] == sensor:
                    temp_set = self.PIDthread.heaters[heatername].setpoint
                    break
            if temp_set > 0:
                self.list_ctrl_temperatures.SetStringItem (pos, 1, "%0.2f" % temp_set)
            else:
                self.list_ctrl_temperatures.SetStringItem (pos, 1, "----")

            temp_is = self.shmem_temperatures[pos]
            self.list_ctrl_temperatures.SetStringItem (pos, 2, "%0.2f" % temp_is)
            mqtt_temperature_dict[sensor] = round (temp_is, 2)

            x_data = self.temp_line[sensor].get_xdata ()

            # update graph only once every temperature_plot_update_interval seconds
            if len (x_data) > 0 and \
                    now - x_data[len (x_data)-1] < \
                    0.00001 * float (config.getGeneral ('plot_update_interval')):
                continue

            x_data = numpy.append (x_data, now)

            self.ydata_temperature[sensor] = numpy.append (self.ydata_temperature[sensor], temp_is)
            if temp_set > 0:
                self.ydata_error[sensor] = numpy.append (self.ydata_error[sensor], temp_is - temp_set)
            else:
                # just put zero as error for a sensor without setpoint
                self.ydata_error[sensor] = numpy.append (self.ydata_error[sensor], 0.)

            if len (x_data) > int (config.getGeneral ('plot_max_points')):
                x_data = x_data[1:-1]
                self.ydata_temperature[sensor] = self.ydata_temperature[sensor][1:-1]
                self.ydata_error[sensor] = self.ydata_error[sensor][1:-1]

            self.temp_line[sensor].set_xdata (x_data)
            if self.plot_error_signal:
                self.temp_line[sensor].set_ydata (self.ydata_error[sensor])
            else:
                self.temp_line[sensor].set_ydata (self.ydata_temperature[sensor])

            plot_changed = True

        if plot_changed:
            self.temp_axes.relim (visible_only = True)
            self.temp_axes.autoscale_view ()
            if self.notebook_main.GetSelection () == 1:
                # do only update figure if monitor notebook page is displayed
                self.temp_figure.canvas.draw ()

            # publish temperature list to MQTT
            self.MqttPublish ("temperatures", mqtt_temperature_dict)

    def updatePowersupplyInfo (self, e = None):
        """Update the powersuppy list and plot with latest values"""

        now = matplotlib.dates.date2num (datetime.now ())
        mqtt_powersupply_dict = {}
        plot_changed = False

        for pos, psu in enumerate (config.getPowersupplyNames ()):
            psu_set = self.shmem_current_setpoints[pos]
            current_is = self.shmem_currents[pos]
            voltage_is = self.shmem_voltages[pos]

            if psu_set >= 0:
                self.list_ctrl_currents.SetStringItem (pos, 1, "%0.2f" % psu_set)
            else:
                self.list_ctrl_currents.SetStringItem (pos, 1, "----")
            self.list_ctrl_currents.SetStringItem (pos, 2, "%0.2f" % current_is)

            # for the rest of the routine treat negative current and voltage values as zero
            current_is = max (0, current_is)
            voltage_is = max (0, voltage_is)

            x_data = self.psu_line[psu].get_xdata ()

            mqtt_powersupply_dict[psu] = {}
            mqtt_powersupply_dict[psu]['I'] = round (current_is, 3)
            mqtt_powersupply_dict[psu]['U'] = round (voltage_is, 3)
            mqtt_powersupply_dict[psu]['P'] = round (voltage_is * current_is, 3)
            if current_is > 0:
                mqtt_powersupply_dict[psu]['R'] = round (voltage_is / current_is, 3)
            else:
                mqtt_powersupply_dict[psu]['R'] = "NaN"

            # update graph only once every powersupply_plot_update_interval seconds
            if len(x_data) > 0 and \
                    now - x_data[len (x_data)-1] < \
                    0.00001 * float (config.getGeneral ('plot_update_interval')):
                continue

            x_data = numpy.append (x_data, now)
            self.ydata_current[psu] = numpy.append (self.ydata_current[psu], current_is)
            self.ydata_power[psu] = numpy.append (self.ydata_power[psu], current_is * voltage_is)

            if len (x_data) > int (config.getGeneral ('plot_max_points')):
                x_data = x_data[1:-1]
                self.ydata_current[psu] = self.ydata_current[psu][1:-1]
                self.ydata_power[psu] = self.ydata_power[psu][1:-1]

            self.psu_line[psu].set_xdata (x_data)
            if self.plot_power_signal:
                self.psu_line[psu].set_ydata (self.ydata_power[psu])
            else:
                self.psu_line[psu].set_ydata (self.ydata_current[psu])

            plot_changed = True

        if plot_changed:
            self.psu_axes.relim (visible_only = True)
            self.psu_axes.autoscale_view ()
            if self.notebook_main.GetSelection () == 1:
                # do only update figure if monitor notebook page is displayed
                self.psu_figure.canvas.draw ()

            # publish powersupply list to MQTT
            self.MqttPublish ("powersupplies", mqtt_powersupply_dict)

    def OnNotebookPageChanged (self, event):
        """Redraw the temperature and current plots if monitor page comes up"""
        self.buzzer.AcknowledgeBeepShort ()
        if self.notebook_main.GetSelection () == 1:
                self.temp_figure.canvas.draw ()
                self.psu_figure.canvas.draw ()

    def OnTempPlotClicked (self, event):
        """Switch flag to plot error_signal on click on temperature plot"""
        self.buzzer.AcknowledgeBeepShort ()
        self.plot_error_signal = not self.plot_error_signal

        # force update of plot
        for sensor in config.getThermocoupleNames ():
            if self.plot_error_signal:
                self.temp_line[sensor].set_ydata (self.ydata_error[sensor])
                self.temp_axes.set_ylabel ("Temperature error (C)", size = 8)
            else:
                self.temp_line[sensor].set_ydata (self.ydata_temperature[sensor])
                self.temp_axes.set_ylabel ("Is temperature (C)", size = 8)

        self.temp_axes.relim (visible_only = True)
        self.temp_axes.autoscale_view ()
        self.temp_figure.canvas.draw ()

    def OnPSUPlotClicked (self, event):
        """Switch flag to plot power_signal on click on powersupply plot"""
        self.buzzer.AcknowledgeBeepShort ()
        self.plot_power_signal = not self.plot_power_signal

        # force update of plot
        for psu in config.getPowersupplyNames ():
            if self.plot_power_signal:
                self.psu_line[psu].set_ydata (self.ydata_power[psu])
                self.psu_axes.set_ylabel ("Is power (W)", size = 8)
            else:
                self.psu_line[psu].set_ydata (self.ydata_current[psu])
                self.psu_axes.set_ylabel ("Is current (A)", size = 8)

        self.psu_axes.relim (visible_only = True)
        self.psu_axes.autoscale_view ()
        self.psu_figure.canvas.draw ()

    def OnTempListDoubleClick (self, event):
        """Mark a temperature list entry for inclusion or exclusion in the plot"""
        self.buzzer.AcknowledgeBeepShort ()
        listpos = event.GetIndex ()
        sensor = event.GetText ()

        if self.list_ctrl_temperatures.GetItemBackgroundColour (listpos) == "white":
            color = self.temp_line[sensor].get_color ()
            self.list_ctrl_temperatures.SetItemBackgroundColour (listpos, self._color_variant (color, 30))
            self.temp_line[sensor].set_visible (True)
        else:
            self.list_ctrl_temperatures.SetItemBackgroundColour (listpos, "white")
            self.temp_line[sensor].set_visible (False)

        self.temp_axes.relim (visible_only = True)
        self.temp_axes.autoscale_view ()
        self.temp_figure.canvas.draw ()

    def OnPsuListDoubleClick (self, event):
        """Mark a powersupply list entry for inclusion or exclusion in the plot"""
        self.buzzer.AcknowledgeBeepShort ()
        listpos = event.GetIndex ()
        sensor = event.GetText ()

        if self.list_ctrl_currents.GetItemBackgroundColour (listpos) == "white":
            color = self.psu_line[sensor].get_color ()
            self.list_ctrl_currents.SetItemBackgroundColour (listpos, self._color_variant (color, 30))
            self.psu_line[sensor].set_visible (True)
        else:
            self.list_ctrl_currents.SetItemBackgroundColour (listpos, "white")
            self.psu_line[sensor].set_visible (False)

        self.psu_axes.relim (visible_only = True)
        self.psu_axes.autoscale_view ()
        self.psu_figure.canvas.draw ()

    """Functions of the heater settings page"""

    def OnHeaterSelected (self, event):
        """Display information on the selected heater on heater settings page"""

        heater = config.getHeater (self.combo_box_heater_sel.GetValue())
        psu = config.getPowersupply (heater['powersupply'])
        max_temp = config.getThermocouple (heater['thermocouple'])['max_temp']

        # Limit setpoint temperature range to be between 
        # low temperature:  20°C and max temperature-10°C
        # high temperature: off temperature and max temperature-10°C
        self.spin_ctrl_low_temp.SetRange (
                20,
                max_temp - 10
                )
        self.spin_ctrl_high_temp.SetRange (
                float (config.getGeneral ('off_state_temperature')),
                max_temp - 10
                )

        self.spin_ctrl_low_temp.SetValue (int (heater['temp_low']))
        self.spin_ctrl_low_p.SetValue (heater['low_pid_p'])
        self.spin_ctrl_low_i.SetValue (heater['low_pid_i'])
        self.spin_ctrl_low_d.SetValue (heater['low_pid_d'])

        self.spin_ctrl_high_temp.SetValue (int (heater['temp_high']))
        self.spin_ctrl_high_p.SetValue (heater['high_pid_p'])
        self.spin_ctrl_high_i.SetValue (heater['high_pid_i'])
        self.spin_ctrl_high_d.SetValue (heater['high_pid_d'])

        self.spin_ctrl_ramp_standard.SetValue (heater['ramp_speed'])
        self.spin_ctrl_ramp_emergency.SetValue (heater['emergency_ramp_speed'])

        self.label_associated_thermocouple.SetLabel (heater['thermocouple'])
        self.label_associated_powersupply.SetLabel ("{} ({} A)".format (
            heater['powersupply'], 
            psu['max_current'] - 0.05
            ))
        self.label_temperature_limit.SetLabel ("{}°C".format (max_temp))

        self.SetTimedStatusText ("Loaded values for heater '{}'.".format (heater['name']), 3)
        self.buzzer.AcknowledgeBeepShort ()

    def OnHeaterApply (self, event):
        """Update and apply new settings for the heater"""

        if self.combo_box_heater_sel.GetValue ():
            heater = config.getHeater (self.combo_box_heater_sel.GetValue ())
        else:
            return

        heater['temp_low'] = self.spin_ctrl_low_temp.GetValue ()
        heater['low_pid_p'] = self.spin_ctrl_low_p.GetValue ()
        heater['low_pid_i'] = self.spin_ctrl_low_i.GetValue ()
        heater['low_pid_d'] = self.spin_ctrl_low_d.GetValue ()

        heater['temp_high'] = self.spin_ctrl_high_temp.GetValue ()
        heater['high_pid_p'] = self.spin_ctrl_high_p.GetValue ()
        heater['high_pid_i'] = self.spin_ctrl_high_i.GetValue ()
        heater['high_pid_d'] = self.spin_ctrl_high_d.GetValue ()

        heater['ramp_speed'] = self.spin_ctrl_ramp_standard.GetValue ()
        heater['emergency_ramp_speed'] = self.spin_ctrl_ramp_emergency.GetValue ()

        for key, value in heater.items():
            config.updateHeaterVal (heater['name'], key, value)
        config.write ()

        # update PID settings of internal PID
        self.PIDthread.heaters[heater['name']].info = heater

        # update setpoints for active heaters
        if self.PIDthread.heaters[heater['name']].state == 'a':
            # if both "if" cases fail, there is a ramp to off active
            if self.oven_status.endswith ('high') and \
               self.PIDthread.heaters[heater['name']].target != heater['temp_high']:
                self.PIDthread.heaters[heater['name']].target = heater['temp_high']
                if not self.oven_status.startswith ('ramp to'):
                    # restart ramp
                    self.totalramptime = self._calculate_ramp_time ()
                    self.gauge_oven_ramp.SetValue (0)
                    self.oven_status = 'ramp to high'
                    for button in self.oven_buttonlist:
                        button.SetBackgroundColour (wx.NullColour)
                    self.button_ramp_high.SetBackgroundColour ((255, 255, 150))
                    self.SetTimedStatusText ("Ramp to High started", 3)
                    self.SetOvenStatusText ("Ramping to High...")
                    self.MqttPublish ("state", "ramp to high", True)
            elif self.oven_status.endswith ('low') and \
               self.PIDthread.heaters[heater['name']].target != heater['temp_low']:
                self.PIDthread.heaters[heater['name']].target = heater['temp_low']
                if not self.oven_status.startswith ('ramp to'):
                    # restart ramp
                    self.totalramptime = self._calculate_ramp_time ()
                    self.gauge_oven_ramp.SetValue (0)
                    self.oven_status = 'ramp to low'
                    for button in self.oven_buttonlist:
                        button.SetBackgroundColour (wx.NullColour)
                    self.button_ramp_low.SetBackgroundColour ((255, 255, 150))
                    self.SetTimedStatusText ("Ramp to Low started", 3)
                    self.SetOvenStatusText ("Ramping to Low...")
                    self.MqttPublish ("state", "ramp to low", True)

        self.SetTimedStatusText ("Applied values for heater '{}' and saved new configuration.".format (heater['name']), 5)
        self.buzzer.AcknowledgeBeepShort ()

    """Functions of the general settings page"""

    def populateRecipients (self):
        """Write all recipients into the TextCtrl"""
        for address in config.getRecipients ():
            self.text_ctrl_recipients.AppendText ("{}\n".format (address))

    def OnMailRecipientsApply (self, event):
        """Update list of mail recipients"""
        recipients = []
        for pos in range (self.text_ctrl_recipients.GetNumberOfLines ()):
            content = self.text_ctrl_recipients.GetLineText (pos)
            if len (content):
                recipients.append (content)

        config.setRecipients (recipients)
        config.write ()
        self.SetTimedStatusText ("Updated mail recipients list and saved new configuration.", 5)
        self.buzzer.AcknowledgeBeepShort ()

    def OnGeneralSettingsApply (self, event):
        """Update settings accessible from the general settings setion"""
        config.updateGeneral ('plot_update_interval', self.spin_ctrl_plot_update_interval.GetValue ())
        config.updateGeneral ('plot_max_points', self.spin_ctrl_plots_max_points.GetValue ())
        config.updateGeneral ('off_state_temperature', self.spin_ctrl_off_state_temp.GetValue ())
        if self.combo_box_db_logging.GetSelection () == 0:
            config.updateDatabase ('logging_enabled', 'True')
        else:
            config.updateDatabase ('logging_enabled', 'False')
        config.write ()
        self.SetTimedStatusText ("Updated general settings and saved new configuration.", 5)
        self.buzzer.AcknowledgeBeepShort ()

    """Functions of the automatic startup page"""

    def OnStartTimerClicked (self, event):
        """Callback function for the Start Timer button.
        So do the necessary checks and start the timer if possible.
        """
        self.buzzer.AcknowledgeBeepShort ()
        # determine selected target
        target = self.radio_box_target_selection.GetSelection ()
        target = {
                  0: 'temp_high',
                  1: 'temp_low',
                  2: 'temp_off'
                 }[target]

        # for ramp to HIGH make sure that some oven is selected
        if target == 'temp_high':
            ovens = self.check_list_box_oven_selection.GetCheckedStrings ()
            if len (ovens) == 0:
                dlg = wx.MessageDialog (self,
                                        "Cannot start ramp timer.\n\n"
                                        "HIGH target needs at least one oven\n"
                                        "to be selected.", "Information",
                                        wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal ()
                dlg.Destroy ()
                self.buzzer.AcknowledgeBeepShort ()
                return
        else:
            ovens = []

        # determine start date/time
        starttime = self.calendar_ctrl.GetDate ()
        starttime.SetHour (self.spin_ctrl_startup_hours.GetValue ())
        starttime.SetMinute (int (self.combo_box_startup_minutes.GetStringSelection ()))
        if starttime <= wx.DateTime.Now ():
                dlg = wx.MessageDialog (self,
                                        "Cannot start ramp timer.\n\n"
                                        "Please select a starting date/time\n"
                                        "that is not in the past.", "Information",
                                        wx.OK|wx.ICON_INFORMATION)
                dlg.ShowModal ()
                dlg.Destroy ()
                self.buzzer.AcknowledgeBeepShort ()
                return

        # save startup information centrally
        self.automatic_startup = {
                'target': target,
                'ovens': ovens,
                'starttime': starttime,
                'timeleft': starttime - wx.DateTime.Now ()
                }

        # make startup selections inactive
        self.check_list_box_oven_selection.Disable ()
        self.radio_box_target_selection.Disable ()
        self.calendar_ctrl.Disable ()
        self.spin_ctrl_startup_hours.Disable ()
        self.combo_box_startup_minutes.Disable ()
        self.button_start_timer.Disable ()
        self.button_stop_timer.Enable ()

        # start timer
        self.startup_timer.Start (1000)
        self.SetTimedStatusText ("Set automatic ramp to begin on {}.".format (starttime), 5)

    def OnStopTimerClicked (self, event):
        """Interrupt a currently running startup timer"""
        self.automatic_startup = None
        self.startup_timer.Stop ()

        # make startup selections active
        self.check_list_box_oven_selection.Enable ()
        self.radio_box_target_selection.Enable ()
        self.calendar_ctrl.Enable ()
        self.spin_ctrl_startup_hours.Enable ()
        self.combo_box_startup_minutes.Enable ()
        self.button_start_timer.Enable ()
        self.button_stop_timer.Disable ()

        # restore original oven status label
        if self.oven_status == 'is high':
            self.label_oven_status.SetLabel ("Oven is in HOT state")
        if self.oven_status == 'is low':
            self.label_oven_status.SetLabel ("Oven is in LOW state")
        if self.oven_status == 'is off':
            self.label_oven_status.SetLabel ("Oven is in OFF state")
        if self.oven_status == 'idle':
            self.label_oven_status.SetLabel ("Oven is idle")
        self.label_oven_status.GetParent().Layout ()

        self.buzzer.AcknowledgeBeepShort ()
        self.SetTimedStatusText ("Automatic ramp cancelled", 3)

    def _calendar_update_lowerdate (self, event = None):
        """Helper function to set calendar lower bound to today"""
        self.calendar_ctrl.SetDateRange (lowerdate = wx.DateTime.Now ())

    def _startup_timer_callback (self, event):
        """Actual startup timer. Print remaining time and do startup"""
        if not self.automatic_startup:
            # no timer running. We shouldn't even have come here
            return

        self.automatic_startup['timeleft'] = \
                self.automatic_startup['starttime'] - wx.DateTime.Now ()

        if not self.automatic_startup['timeleft'].IsPositive ():
            # start the selected ramp
            if self.automatic_startup['target'] == 'temp_high':
                # select necessary ovens
                for name, button in self.button_oven.items ():
                    if name in self.automatic_startup['ovens']:
                        button.SetValue (1)
                        button.SetBackgroundColour ((150, 255, 150))
                    else:
                        button.SetValue (0)
                        button.SetBackgroundColour (wx.NullColour)
                self.OnHighClicked (automatic = True)
            if self.automatic_startup['target'] == 'temp_low':
                self.OnLowClicked (automatic = True)
            if self.automatic_startup['target'] == 'temp_off':
                self.OnOffClicked (automatic = True)

            # bring the program back to a state without startup timer
            self.automatic_startup = None
            self.startup_timer.Stop ()
            self.check_list_box_oven_selection.Enable ()
            self.radio_box_target_selection.Enable ()
            self.calendar_ctrl.Enable ()
            self.spin_ctrl_startup_hours.Enable ()
            self.combo_box_startup_minutes.Enable ()
            self.button_start_timer.Enable ()
            self.button_stop_timer.Disable ()
        elif self.oven_status in ['is high', 'is off', 'is low', 'idle']:
            # print remaining time till ramp start
            minutes, seconds = divmod (self.automatic_startup['timeleft'].GetSeconds (), 60)
            hours, minutes = divmod (minutes, 60)
            time_string = "%02d:%02d:%02d" % (hours, minutes, seconds)
            # why the added space in front if 'Remaining' below:
            # This is to prevent the test for startswith("Remaining ") to trigger
            # in the _status_timer_callback() function that would otherwise think
            # a ramp just finished and overwrite the status label again.
            self.label_oven_status.SetLabel (" Remaining time till automatic ramp start: " + time_string + " ")
            self.label_oven_status.GetParent().Layout ()


class OvenControlGUI (wx.App):
    def OnInit (self):
        self.frame = MainWindow (None, wx.ID_ANY, style = wx.NO_BORDER|wx.STAY_ON_TOP)
        self.SetTopWindow (self.frame)
        self.frame.Show ()
        self.frame.Maximize (True)
        return True


if __name__ == "__main__":
    app = OvenControlGUI (0)
    app.MainLoop ()
