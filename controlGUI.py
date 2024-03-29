#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.8.3 on Fri Aug 17 09:12:53 2018
#

import wx
import wx.calendar

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class ControlGUI(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ControlGUI.__init__
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((800, 480))
        self.statusbar = self.CreateStatusBar(2)
        self.notebook_main = wx.Notebook(self, wx.ID_ANY)
        self.page_control = wx.Panel(self.notebook_main, wx.ID_ANY)
        self.button_ramp_high = wx.ToggleButton(self.page_control, wx.ID_ANY, "Ramp selected to HIGH")
        self.button_ramp_low = wx.ToggleButton(self.page_control, wx.ID_ANY, "Ramp all to LOW")
        self.button_ramp_off = wx.ToggleButton(self.page_control, wx.ID_ANY, "Ramp all to OFF")
        self.button_ramp_emergency = wx.ToggleButton(self.page_control, wx.ID_ANY, "Emergency ramp to OFF")
        self.label_interlock_water = wx.StaticText(self.page_control, wx.ID_ANY, "Chiller", style=wx.ALIGN_CENTER)
        self.label_interlock_temp = wx.StaticText(self.page_control, wx.ID_ANY, "Temperature", style=wx.ALIGN_CENTER)
        self.label_interlock_heater = wx.StaticText(self.page_control, wx.ID_ANY, "Heater", style=wx.ALIGN_CENTER)
        self.label_interlock_powersupply = wx.StaticText(self.page_control, wx.ID_ANY, "Power supply", style=wx.ALIGN_CENTER)
        self.label_interlock_ups = wx.StaticText(self.page_control, wx.ID_ANY, "UPS", style=wx.ALIGN_CENTER)
        self.label_oven_status = wx.StaticText(self.page_control, wx.ID_ANY, "Oven is idle", style=wx.ALIGN_CENTER)
        self.gauge_oven_ramp = wx.Gauge(self.page_control, wx.ID_ANY, 100)
        self.page_monitor = wx.Panel(self.notebook_main, wx.ID_ANY)
        self.list_ctrl_temperatures = wx.ListCtrl(self.page_monitor, wx.ID_ANY, style=wx.LC_REPORT)
        self.list_ctrl_currents = wx.ListCtrl(self.page_monitor, wx.ID_ANY, style=wx.LC_REPORT)
        self.page_settings_heater = wx.Panel(self.notebook_main, wx.ID_ANY)
        self.combo_box_heater_sel = wx.ComboBox(self.page_settings_heater, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.button_heater_settings_apply = wx.Button(self.page_settings_heater, wx.ID_APPLY, "")
        self.button_heater_settings_undo = wx.Button(self.page_settings_heater, wx.ID_UNDO, "")
        self.spin_ctrl_low_temp = wx.SpinCtrl(self.page_settings_heater, wx.ID_ANY, "0", min=0, max=1500)
        self.spin_ctrl_low_p = wx.SpinCtrlDouble(self.page_settings_heater, wx.ID_ANY, "0", min=0.0, max=5000.0)
        self.spin_ctrl_low_i = wx.SpinCtrlDouble(self.page_settings_heater, wx.ID_ANY, "0", min=0.0, max=5000.0)
        self.spin_ctrl_low_d = wx.SpinCtrlDouble(self.page_settings_heater, wx.ID_ANY, "0", min=0.0, max=5000.0)
        self.spin_ctrl_high_temp = wx.SpinCtrl(self.page_settings_heater, wx.ID_ANY, "0", min=0, max=1500)
        self.spin_ctrl_high_p = wx.SpinCtrlDouble(self.page_settings_heater, wx.ID_ANY, "0", min=0.0, max=5000.0)
        self.spin_ctrl_high_i = wx.SpinCtrlDouble(self.page_settings_heater, wx.ID_ANY, "0", min=0.0, max=5000.0)
        self.spin_ctrl_high_d = wx.SpinCtrlDouble(self.page_settings_heater, wx.ID_ANY, "0", min=0.0, max=5000.0)
        self.spin_ctrl_ramp_standard = wx.SpinCtrlDouble(self.page_settings_heater, wx.ID_ANY, "0", min=0, max=100)
        self.spin_ctrl_ramp_emergency = wx.SpinCtrlDouble(self.page_settings_heater, wx.ID_ANY, "0", min=0, max=100)
        self.label_associated_powersupply = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "", style=wx.ALIGN_LEFT)
        self.label_associated_sensor = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Associated thermocouple", style=wx.ALIGN_RIGHT)
        self.label_associated_thermocouple = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "", style=wx.ALIGN_LEFT)
        self.label_maximum_temperature = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Maximum temperature", style=wx.ALIGN_RIGHT)
        self.label_temperature_limit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "", style=wx.ALIGN_LEFT)
        self.page_settings_general = wx.Panel(self.notebook_main, wx.ID_ANY)
        self.text_ctrl_recipients = wx.TextCtrl(self.page_settings_general, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.button_recipients_apply = wx.Button(self.page_settings_general, wx.ID_ANY, "Apply mail settings")
        self.spin_ctrl_plot_update_interval = wx.SpinCtrl(self.page_settings_general, wx.ID_ANY, "", min=2, max=60)
        self.spin_ctrl_plots_max_points = wx.SpinCtrl(self.page_settings_general, wx.ID_ANY, "", min=10, max=3600)
        self.spin_ctrl_off_state_temp = wx.SpinCtrl(self.page_settings_general, wx.ID_ANY, "30", min=10, max=300)
        self.combo_box_db_logging = wx.ComboBox(self.page_settings_general, wx.ID_ANY, choices=["enabled", "disabled"], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.button_general_apply = wx.Button(self.page_settings_general, wx.ID_ANY, "Apply general settings")
        self.button_exit = wx.Button(self.page_settings_general, wx.ID_EXIT, "")
        self.notebook_main_Automaticstartup = wx.Panel(self.notebook_main, wx.ID_ANY)
        self.check_list_box_oven_selection = wx.CheckListBox(self.notebook_main_Automaticstartup, wx.ID_ANY, choices=[])
        self.radio_box_target_selection = wx.RadioBox(self.notebook_main_Automaticstartup, wx.ID_ANY, "", choices=["Ramp selected ovens to HIGH", "Ramp all ovens to LOW", "Ramp all ovens to OFF"], majorDimension=3, style=wx.RA_SPECIFY_ROWS)
        self.calendar_ctrl = wx.calendar.CalendarCtrl(self.notebook_main_Automaticstartup, wx.ID_ANY, style=wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION | wx.calendar.CAL_SHOW_HOLIDAYS | wx.calendar.CAL_SHOW_SURROUNDING_WEEKS | wx.calendar.CAL_SUNDAY_FIRST)
        self.spin_ctrl_startup_hours = wx.SpinCtrl(self.notebook_main_Automaticstartup, wx.ID_ANY, "8", min=0, max=23, style=wx.ALIGN_RIGHT | wx.SP_ARROW_KEYS | wx.SP_WRAP)
        self.combo_box_startup_minutes = wx.ComboBox(self.notebook_main_Automaticstartup, wx.ID_ANY, choices=["00", "15", "30", "45"], style=wx.CB_DROPDOWN)
        self.button_start_timer = wx.Button(self.notebook_main_Automaticstartup, wx.ID_ANY, "START timer")
        self.button_stop_timer = wx.Button(self.notebook_main_Automaticstartup, wx.ID_ANY, "STOP timer")

        self.__set_properties()
        self.__do_layout()

        self.label_interlock_water.Bind(wx.EVT_LEFT_DCLICK, self.OnInterlockDClicked)
        self.label_interlock_temp.Bind(wx.EVT_LEFT_DCLICK, self.OnInterlockDClicked)
        self.label_interlock_heater.Bind(wx.EVT_LEFT_DCLICK, self.OnInterlockDClicked)
        self.label_interlock_powersupply.Bind(wx.EVT_LEFT_DCLICK, self.OnInterlockDClicked)
        self.label_interlock_ups.Bind(wx.EVT_LEFT_DCLICK, self.OnInterlockDClicked)

        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnHighClicked, self.button_ramp_high)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnLowClicked, self.button_ramp_low)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnOffClicked, self.button_ramp_off)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnEmergencyClicked, self.button_ramp_emergency)
        self.Bind(wx.EVT_COMBOBOX, self.OnHeaterSelected, self.combo_box_heater_sel)
        self.Bind(wx.EVT_BUTTON, self.OnHeaterApply, self.button_heater_settings_apply)
        self.Bind(wx.EVT_BUTTON, self.OnHeaterSelected, self.button_heater_settings_undo)
        self.Bind(wx.EVT_BUTTON, self.OnMailRecipientsApply, self.button_recipients_apply)
        self.Bind(wx.EVT_BUTTON, self.OnGeneralSettingsApply, self.button_general_apply)
        self.Bind(wx.EVT_BUTTON, self.OnExit, self.button_exit)
        self.Bind(wx.EVT_BUTTON, self.OnStartTimerClicked, self.button_start_timer)
        self.Bind(wx.EVT_BUTTON, self.OnStopTimerClicked, self.button_stop_timer)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnNotebookPageChanged, self.notebook_main)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ControlGUI.__set_properties
        self.SetTitle("ErYbLi-oven control")
        _icon = wx.NullIcon
        _icon.CopyFromBitmap(wx.Bitmap("ErYbLi-oven_icon.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        self.statusbar.SetStatusWidths([-2, -1])

        # statusbar fields
        statusbar_fields = ["application status", "oven status"]
        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)
        self.label_interlock_water.SetBackgroundColour(wx.Colour(0, 255, 0))
        self.label_interlock_water.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.label_interlock_temp.SetBackgroundColour(wx.Colour(0, 255, 0))
        self.label_interlock_temp.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.label_interlock_heater.SetBackgroundColour(wx.Colour(0, 255, 0))
        self.label_interlock_heater.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.label_interlock_powersupply.SetBackgroundColour(wx.Colour(0, 255, 0))
        self.label_interlock_powersupply.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.label_interlock_ups.SetBackgroundColour(wx.Colour(0, 255, 0))
        self.label_interlock_ups.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.label_oven_status.SetFont(wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.list_ctrl_temperatures.SetMinSize((200, -1))
        self.list_ctrl_temperatures.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.list_ctrl_temperatures.InsertColumn(0, "Sensor", format=wx.LIST_FORMAT_LEFT, width=100)
        self.list_ctrl_temperatures.InsertColumn(1, u"Set (\u00b0C)", format=wx.LIST_FORMAT_LEFT, width=50)
        self.list_ctrl_temperatures.InsertColumn(2, u"Is (\u00b0C)", format=wx.LIST_FORMAT_LEFT, width=50)
        self.list_ctrl_currents.SetMinSize((200, -1))
        self.list_ctrl_currents.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.list_ctrl_currents.InsertColumn(0, "Sensor", format=wx.LIST_FORMAT_LEFT, width=100)
        self.list_ctrl_currents.InsertColumn(1, "Set (A)", format=wx.LIST_FORMAT_LEFT, width=50)
        self.list_ctrl_currents.InsertColumn(2, "Is (A)", format=wx.LIST_FORMAT_LEFT, width=50)
        self.combo_box_heater_sel.SetMinSize((300, 34))
        self.button_heater_settings_apply.SetToolTip(wx.ToolTip("Use 'Apply' to apply and immediately use the settings of the current heater."))
        self.button_heater_settings_apply.SetDefault()
        self.button_heater_settings_undo.SetToolTip(wx.ToolTip("Use 'Undo' to revert any changes of the current heater to the actual ones."))
        self.text_ctrl_recipients.SetToolTip(wx.ToolTip("Add one e-mail address per line please."))
        self.button_recipients_apply.SetToolTip(wx.ToolTip("Apply and save changes to list of recipients"))
        self.spin_ctrl_plot_update_interval.SetToolTip(wx.ToolTip("Time in seconds between redraws of the temperature and current plots."))
        self.spin_ctrl_plots_max_points.SetToolTip(wx.ToolTip("Maximum number of points to be displayed in the temperature and current plots."))
        self.spin_ctrl_off_state_temp.SetToolTip(wx.ToolTip("Target temperature when ramping the oven to the OFF state."))
        self.combo_box_db_logging.SetToolTip(wx.ToolTip("Whether to enable logging of temperature and current information to an external MySQL database."))
        self.combo_box_db_logging.SetSelection(0)
        self.button_general_apply.SetToolTip(wx.ToolTip("Apply and save general setting changes"))
        self.button_exit.SetToolTip(wx.ToolTip("Exit the control program.\nUse carefully considering the state of the oven system."))
        self.check_list_box_oven_selection.SetToolTip(wx.ToolTip("Choose which ovens to include in a ramp to HIGH"))
        self.radio_box_target_selection.SetToolTip(wx.ToolTip("Choose which ramp to perform"))
        self.radio_box_target_selection.SetSelection(0)
        self.spin_ctrl_startup_hours.SetMinSize((110, 34))
        self.spin_ctrl_startup_hours.SetToolTip(wx.ToolTip("Hours part of ramp start time"))
        self.combo_box_startup_minutes.SetMinSize((70, 34))
        self.combo_box_startup_minutes.SetToolTip(wx.ToolTip("Minutes part of ramp start time"))
        self.combo_box_startup_minutes.SetSelection(0)
        self.button_stop_timer.Enable(False)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ControlGUI.__do_layout
        self.sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_startup_vert1 = wx.BoxSizer(wx.VERTICAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_startup_horiz1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_startup_vert3 = wx.StaticBoxSizer(wx.StaticBox(self.notebook_main_Automaticstartup, wx.ID_ANY, "Date / Time selection"), wx.HORIZONTAL)
        sizer_vert_schedule = wx.BoxSizer(wx.VERTICAL)
        sizer_horiz_schedule = wx.BoxSizer(wx.HORIZONTAL)
        sizer_startup_vert2 = wx.StaticBoxSizer(wx.StaticBox(self.notebook_main_Automaticstartup, wx.ID_ANY, "Oven / Target selection"), wx.VERTICAL)
        sizer_vert_general1 = wx.BoxSizer(wx.VERTICAL)
        sizer_horiz_general2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_vert_about = wx.StaticBoxSizer(wx.StaticBox(self.page_settings_general, wx.ID_ANY, "About ErYbLi-oven control"), wx.VERTICAL)
        sizer_horiz_general1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_vert_genset = wx.StaticBoxSizer(wx.StaticBox(self.page_settings_general, wx.ID_ANY, "General settings"), wx.VERTICAL)
        grid_sizer_genset = wx.FlexGridSizer(4, 3, 3, 10)
        sizer_vert_notifiy = wx.StaticBoxSizer(wx.StaticBox(self.page_settings_general, wx.ID_ANY, "Notification settings"), wx.VERTICAL)
        sizer_vert_main = wx.BoxSizer(wx.VERTICAL)
        sizer_vert_heater_details1 = wx.StaticBoxSizer(wx.StaticBox(self.page_settings_heater, wx.ID_ANY, "Heater details"), wx.VERTICAL)
        sizer_vert_heater_details2 = wx.BoxSizer(wx.VERTICAL)
        sizer_horiz_heater_details2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_vert_heater_details4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_further_info = wx.FlexGridSizer(3, 2, 5, 0)
        sizer_vert_heater_details3 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_ramp_speeds = wx.FlexGridSizer(0, 3, 5, 0)
        sizer_horiz_heater_details1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_vert_high_temp = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_high_temp = wx.FlexGridSizer(0, 3, 5, 0)
        sizer_vert_low_temp = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_low_temp = wx.FlexGridSizer(0, 3, 5, 0)
        sizer_horiz_heater_sel = wx.BoxSizer(wx.HORIZONTAL)
        sizer_vert_monitor = wx.BoxSizer(wx.VERTICAL)
        self.sizer_horiz_current = wx.StaticBoxSizer(wx.StaticBox(self.page_monitor, wx.ID_ANY, "Power supplies"), wx.HORIZONTAL)
        self.sizer_horiz_temp = wx.StaticBoxSizer(wx.StaticBox(self.page_monitor, wx.ID_ANY, "Oven temperatures"), wx.HORIZONTAL)
        sizer_vert_control1 = wx.BoxSizer(wx.VERTICAL)
        sizer_vert_control_status = wx.StaticBoxSizer(wx.StaticBox(self.page_control, wx.ID_ANY, "Oven status"), wx.VERTICAL)
        sizer_horiz_control_interlock = wx.BoxSizer(wx.HORIZONTAL)
        sizer_horiz_control_action = wx.StaticBoxSizer(wx.StaticBox(self.page_control, wx.ID_ANY, "Action selection"), wx.HORIZONTAL)
        sizer_horizontal_control1 = wx.StaticBoxSizer(wx.StaticBox(self.page_control, wx.ID_ANY, "Oven selection"), wx.HORIZONTAL)
        self.sizer_horiz_oven_selection = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_horiz_oven_selection.Add((0, 0), 0, 0, 0)
        sizer_horizontal_control1.Add(self.sizer_horiz_oven_selection, 1, wx.ALL | wx.EXPAND, 10)
        sizer_vert_control1.Add(sizer_horizontal_control1, 2, wx.ALL | wx.EXPAND, 10)
        sizer_horiz_control_action.Add(self.button_ramp_high, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.TOP, 10)
        sizer_horiz_control_action.Add(self.button_ramp_low, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.TOP, 10)
        sizer_horiz_control_action.Add(self.button_ramp_off, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.TOP, 10)
        sizer_horiz_control_action.Add(self.button_ramp_emergency, 1, wx.ALL | wx.EXPAND, 10)
        sizer_vert_control1.Add(sizer_horiz_control_action, 2, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer_horiz_control_interlock.Add(self.label_interlock_water, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.TOP, 10)
        sizer_horiz_control_interlock.Add(self.label_interlock_temp, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.TOP, 10)
        sizer_horiz_control_interlock.Add(self.label_interlock_heater, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.TOP, 10)
        sizer_horiz_control_interlock.Add(self.label_interlock_powersupply, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.TOP, 10)
        sizer_horiz_control_interlock.Add(self.label_interlock_ups, 1, wx.ALL | wx.EXPAND, 10)
        sizer_vert_control_status.Add(sizer_horiz_control_interlock, 0, wx.ALL | wx.EXPAND, 0)
        sizer_vert_control_status.Add(self.label_oven_status, 0, wx.ALL | wx.EXPAND, 5)
        sizer_vert_control_status.Add(self.gauge_oven_ramp, 0, wx.ALL | wx.EXPAND, 5)
        sizer_vert_control1.Add(sizer_vert_control_status, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        self.page_control.SetSizer(sizer_vert_control1)
        self.sizer_horiz_temp.Add(self.list_ctrl_temperatures, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        sizer_vert_monitor.Add(self.sizer_horiz_temp, 1, wx.ALL | wx.EXPAND, 10)
        self.sizer_horiz_current.Add(self.list_ctrl_currents, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        sizer_vert_monitor.Add(self.sizer_horiz_current, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        self.page_monitor.SetSizer(sizer_vert_monitor)
        sizer_vert_main.Add((1, 1), 1, wx.EXPAND, 0)
        label_heater_sel = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Heater selection", style=wx.ALIGN_RIGHT)
        label_heater_sel.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_horiz_heater_sel.Add(label_heater_sel, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_horiz_heater_sel.Add(self.combo_box_heater_sel, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_horiz_heater_sel.Add((1, 1), 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_horiz_heater_sel.Add(self.button_heater_settings_apply, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_horiz_heater_sel.Add(self.button_heater_settings_undo, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP, 10)
        sizer_vert_main.Add(sizer_horiz_heater_sel, 1, wx.ALL | wx.EXPAND, 5)
        sizer_vert_main.Add((1, 1), 1, wx.EXPAND, 0)
        label_low_temp_settings = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Low temperature settings")
        label_low_temp_settings.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_vert_low_temp.Add(label_low_temp_settings, 0, wx.EXPAND | wx.LEFT, 10)
        label_low_temp = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Temperature", style=wx.ALIGN_RIGHT)
        label_low_temp.SetMinSize((120, 17))
        grid_sizer_low_temp.Add(label_low_temp, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_low_temp.Add(self.spin_ctrl_low_temp, 0, 0, 0)
        label_low_temp_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"\u00b0C")
        grid_sizer_low_temp.Add(label_low_temp_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label_low_p = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "PID proportional", style=wx.ALIGN_RIGHT)
        grid_sizer_low_temp.Add(label_low_p, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_low_temp.Add(self.spin_ctrl_low_p, 0, 0, 0)
        label_low_p_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"mA/\u00b0C")
        grid_sizer_low_temp.Add(label_low_p_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label_low_i = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "PID integral", style=wx.ALIGN_RIGHT)
        grid_sizer_low_temp.Add(label_low_i, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_low_temp.Add(self.spin_ctrl_low_i, 0, 0, 0)
        label_low_i_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"mA/(\u00b0C s)")
        grid_sizer_low_temp.Add(label_low_i_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label_low_d = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "PID derivative", style=wx.ALIGN_RIGHT)
        grid_sizer_low_temp.Add(label_low_d, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_low_temp.Add(self.spin_ctrl_low_d, 0, 0, 0)
        label_low_d_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"mA/(\u00b0C / s)")
        grid_sizer_low_temp.Add(label_low_d_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer_vert_low_temp.Add(grid_sizer_low_temp, 1, wx.ALL | wx.EXPAND, 5)
        sizer_horiz_heater_details1.Add(sizer_vert_low_temp, 1, wx.EXPAND, 0)
        static_line_vert1 = wx.StaticLine(self.page_settings_heater, wx.ID_ANY, style=wx.LI_VERTICAL)
        sizer_horiz_heater_details1.Add(static_line_vert1, 0, wx.EXPAND, 0)
        label_high_temp_settings = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "High temperature settings")
        label_high_temp_settings.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_vert_high_temp.Add(label_high_temp_settings, 0, wx.EXPAND | wx.LEFT, 10)
        label_high_temp = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Temperature", style=wx.ALIGN_RIGHT)
        label_high_temp.SetMinSize((120, 17))
        grid_sizer_high_temp.Add(label_high_temp, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_high_temp.Add(self.spin_ctrl_high_temp, 0, 0, 0)
        label_high_temp_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"\u00b0C")
        grid_sizer_high_temp.Add(label_high_temp_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label_high_p = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "PID proportional", style=wx.ALIGN_RIGHT)
        grid_sizer_high_temp.Add(label_high_p, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_high_temp.Add(self.spin_ctrl_high_p, 0, 0, 0)
        label_high_p_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"mA/\u00b0C")
        grid_sizer_high_temp.Add(label_high_p_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label_high_i = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "PID integral", style=wx.ALIGN_RIGHT)
        grid_sizer_high_temp.Add(label_high_i, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_high_temp.Add(self.spin_ctrl_high_i, 0, 0, 0)
        label_high_i_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"mA/(\u00b0C s)")
        grid_sizer_high_temp.Add(label_high_i_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label_high_d = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "PID derivative", style=wx.ALIGN_RIGHT)
        grid_sizer_high_temp.Add(label_high_d, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_high_temp.Add(self.spin_ctrl_high_d, 0, 0, 0)
        label_high_d_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"mA/(\u00b0C / s)")
        grid_sizer_high_temp.Add(label_high_d_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer_vert_high_temp.Add(grid_sizer_high_temp, 1, wx.ALL | wx.EXPAND, 5)
        sizer_horiz_heater_details1.Add(sizer_vert_high_temp, 1, wx.EXPAND, 0)
        sizer_vert_heater_details2.Add(sizer_horiz_heater_details1, 0, wx.EXPAND, 0)
        static_line_horiz = wx.StaticLine(self.page_settings_heater, wx.ID_ANY)
        sizer_vert_heater_details2.Add(static_line_horiz, 0, wx.EXPAND, 0)
        label_ramp_speed_settings = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Ramp speed settings")
        label_ramp_speed_settings.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_vert_heater_details3.Add(label_ramp_speed_settings, 0, wx.EXPAND | wx.LEFT, 10)
        label_ramp_standard = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Standard ramp", style=wx.ALIGN_RIGHT)
        label_ramp_standard.SetMinSize((120, 17))
        grid_sizer_ramp_speeds.Add(label_ramp_standard, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_ramp_speeds.Add(self.spin_ctrl_ramp_standard, 0, 0, 0)
        label_ramp_standard_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"\u00b0C/min")
        grid_sizer_ramp_speeds.Add(label_ramp_standard_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        label_ramp_emergency = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Emergency ramp", style=wx.ALIGN_RIGHT)
        label_ramp_emergency.SetMinSize((120, 17))
        grid_sizer_ramp_speeds.Add(label_ramp_emergency, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 5)
        grid_sizer_ramp_speeds.Add(self.spin_ctrl_ramp_emergency, 0, 0, 0)
        label_ramp_emergency_unit = wx.StaticText(self.page_settings_heater, wx.ID_ANY, u"\u00b0C/min")
        grid_sizer_ramp_speeds.Add(label_ramp_emergency_unit, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer_vert_heater_details3.Add(grid_sizer_ramp_speeds, 1, wx.ALL | wx.EXPAND, 5)
        sizer_horiz_heater_details2.Add(sizer_vert_heater_details3, 1, wx.EXPAND | wx.TOP, 5)
        static_line_vert2 = wx.StaticLine(self.page_settings_heater, wx.ID_ANY, style=wx.LI_VERTICAL)
        sizer_horiz_heater_details2.Add(static_line_vert2, 0, wx.EXPAND, 0)
        label_further_info = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Further information")
        label_further_info.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_vert_heater_details4.Add(label_further_info, 0, wx.EXPAND | wx.LEFT, 10)
        label_associated_psu = wx.StaticText(self.page_settings_heater, wx.ID_ANY, "Associated powersupply", style=wx.ALIGN_RIGHT)
        grid_sizer_further_info.Add(label_associated_psu, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 5)
        grid_sizer_further_info.Add(self.label_associated_powersupply, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        grid_sizer_further_info.Add(self.label_associated_sensor, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 5)
        grid_sizer_further_info.Add(self.label_associated_thermocouple, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        grid_sizer_further_info.Add(self.label_maximum_temperature, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 5)
        grid_sizer_further_info.Add(self.label_temperature_limit, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        grid_sizer_further_info.AddGrowableRow(0)
        grid_sizer_further_info.AddGrowableRow(1)
        sizer_vert_heater_details4.Add(grid_sizer_further_info, 1, wx.ALL | wx.EXPAND, 5)
        sizer_horiz_heater_details2.Add(sizer_vert_heater_details4, 1, wx.EXPAND | wx.TOP, 5)
        sizer_vert_heater_details2.Add(sizer_horiz_heater_details2, 1, wx.EXPAND, 0)
        sizer_vert_heater_details1.Add(sizer_vert_heater_details2, 0, wx.ALL | wx.EXPAND, 5)
        sizer_vert_main.Add(sizer_vert_heater_details1, 2, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        self.page_settings_heater.SetSizer(sizer_vert_main)
        label_mail_recipients = wx.StaticText(self.page_settings_general, wx.ID_ANY, "Mail recipients")
        label_mail_recipients.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_vert_notifiy.Add(label_mail_recipients, 0, wx.ALL | wx.EXPAND, 10)
        sizer_vert_notifiy.Add(self.text_ctrl_recipients, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer_vert_notifiy.Add(self.button_recipients_apply, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT, 10)
        sizer_horiz_general1.Add(sizer_vert_notifiy, 1, wx.ALL | wx.EXPAND, 10)
        label_plots_update_interval = wx.StaticText(self.page_settings_general, wx.ID_ANY, "Plots update interval")
        grid_sizer_genset.Add(label_plots_update_interval, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)
        grid_sizer_genset.Add(self.spin_ctrl_plot_update_interval, 1, wx.EXPAND, 0)
        label_plots_update_interval_unit = wx.StaticText(self.page_settings_general, wx.ID_ANY, "s")
        grid_sizer_genset.Add(label_plots_update_interval_unit, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        label_plots_max_points = wx.StaticText(self.page_settings_general, wx.ID_ANY, "Plots max. points", style=wx.ALIGN_RIGHT)
        grid_sizer_genset.Add(label_plots_max_points, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)
        grid_sizer_genset.Add(self.spin_ctrl_plots_max_points, 1, wx.EXPAND, 0)
        grid_sizer_genset.Add((1, 1), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        label_off_state_temp = wx.StaticText(self.page_settings_general, wx.ID_ANY, "Off state temperature")
        grid_sizer_genset.Add(label_off_state_temp, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)
        grid_sizer_genset.Add(self.spin_ctrl_off_state_temp, 1, wx.EXPAND, 0)
        label_off_state_temp_unit = wx.StaticText(self.page_settings_general, wx.ID_ANY, u"\u00b0C")
        grid_sizer_genset.Add(label_off_state_temp_unit, 0, wx.ALIGN_CENTER, 0)
        label_db_logging = wx.StaticText(self.page_settings_general, wx.ID_ANY, "Database logging")
        grid_sizer_genset.Add(label_db_logging, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)
        grid_sizer_genset.Add(self.combo_box_db_logging, 1, wx.EXPAND, 0)
        grid_sizer_genset.Add((1, 1), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_genset.AddGrowableCol(0)
        grid_sizer_genset.AddGrowableCol(1)
        sizer_vert_genset.Add(grid_sizer_genset, 1, wx.ALL | wx.EXPAND, 10)
        sizer_vert_genset.Add(self.button_general_apply, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT, 10)
        sizer_horiz_general1.Add(sizer_vert_genset, 1, wx.BOTTOM | wx.EXPAND | wx.RIGHT | wx.TOP, 10)
        sizer_vert_general1.Add(sizer_horiz_general1, 1, wx.EXPAND, 0)
        label_about = wx.StaticText(self.page_settings_general, wx.ID_ANY, u"Brought to you by Florian Schaefer <schaefer AT scphys.kyoto-u.ac.jp>.\n\u00a9 Quantum Optics Group, Kyoto University, 2018-2020\n\nVersion: 2020/10/29")
        sizer_vert_about.Add(label_about, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        sizer_horiz_general2.Add(sizer_vert_about, 1, wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer_horiz_general2.Add(self.button_exit, 0, wx.ALIGN_BOTTOM | wx.BOTTOM | wx.RIGHT | wx.TOP, 10)
        sizer_vert_general1.Add(sizer_horiz_general2, 1, wx.EXPAND, 0)
        self.page_settings_general.SetSizer(sizer_vert_general1)
        label_oven_selection = wx.StaticText(self.notebook_main_Automaticstartup, wx.ID_ANY, "Oven selection")
        label_oven_selection.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_startup_vert2.Add(label_oven_selection, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_startup_vert2.Add(self.check_list_box_oven_selection, 1, wx.ALL | wx.EXPAND, 10)
        label_target_selection = wx.StaticText(self.notebook_main_Automaticstartup, wx.ID_ANY, "Target selection")
        label_target_selection.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        sizer_startup_vert2.Add(label_target_selection, 0, wx.LEFT | wx.TOP, 10)
        sizer_startup_vert2.Add(self.radio_box_target_selection, 1, wx.BOTTOM | wx.LEFT | wx.RIGHT, 10)
        self.sizer_startup_horiz1.Add(sizer_startup_vert2, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_vert_schedule.Add(self.calendar_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        label_ramp_begin_time = wx.StaticText(self.notebook_main_Automaticstartup, wx.ID_ANY, "Begin of ramp time")
        sizer_horiz_schedule.Add(label_ramp_begin_time, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT, 10)
        sizer_horiz_schedule.Add(self.spin_ctrl_startup_hours, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 10)
        label_colon = wx.StaticText(self.notebook_main_Automaticstartup, wx.ID_ANY, " : ", style=wx.ALIGN_CENTER)
        label_colon.SetMinSize((10, 17))
        sizer_horiz_schedule.Add(label_colon, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 10)
        sizer_horiz_schedule.Add(self.combo_box_startup_minutes, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 10)
        sizer_horiz_schedule.Add((1, 1), 1, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        sizer_vert_schedule.Add(sizer_horiz_schedule, 0, wx.EXPAND | wx.TOP, 20)
        sizer_startup_vert3.Add(sizer_vert_schedule, 2, wx.ALL | wx.EXPAND, 10)
        self.sizer_startup_horiz1.Add(sizer_startup_vert3, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer_startup_vert1.Add(self.sizer_startup_horiz1, 1, wx.ALL | wx.EXPAND, 0)
        sizer_6.Add((10, 10), 1, wx.ALIGN_CENTER, 0)
        sizer_6.Add(self.button_start_timer, 0, wx.BOTTOM | wx.LEFT | wx.TOP, 10)
        sizer_6.Add(self.button_stop_timer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        sizer_startup_vert1.Add(sizer_6, 0, wx.ALL | wx.EXPAND, 0)
        self.notebook_main_Automaticstartup.SetSizer(sizer_startup_vert1)
        self.notebook_main.AddPage(self.page_control, "Control")
        self.notebook_main.AddPage(self.page_monitor, "Monitor")
        self.notebook_main.AddPage(self.page_settings_heater, "Heater settings")
        self.notebook_main.AddPage(self.page_settings_general, "General settings")
        self.notebook_main.AddPage(self.notebook_main_Automaticstartup, "Automatic startup")
        self.sizer_main.Add(self.notebook_main, 1, wx.EXPAND, 0)
        self.SetSizer(self.sizer_main)
        self.Layout()
        # end wxGlade

    def OnHighClicked(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnHighClicked' not implemented!")
        event.Skip()

    def OnLowClicked(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnLowClicked' not implemented!")
        event.Skip()

    def OnOffClicked(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnOffClicked' not implemented!")
        event.Skip()

    def OnEmergencyClicked(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnEmergencyClicked' not implemented!")
        event.Skip()

    def OnInterlockDClicked(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnInterlockDClicked' not implemented!")
        event.Skip()

    def OnHeaterSelected(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnHeaterSelected' not implemented!")
        event.Skip()

    def OnHeaterApply(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnHeaterApply' not implemented!")
        event.Skip()

    def OnMailRecipientsApply(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnMailRecipientsApply' not implemented!")
        event.Skip()

    def OnGeneralSettingsApply(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnGeneralSettingsApply' not implemented!")
        event.Skip()

    def OnExit(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnExit' not implemented!")
        event.Skip()

    def OnStartTimerClicked(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnStartTimerClicked' not implemented!")
        event.Skip()

    def OnStopTimerClicked(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnStopTimerClicked' not implemented!")
        event.Skip()

    def OnNotebookPageChanged(self, event):  # wxGlade: ControlGUI.<event_handler>
        print("Event handler 'OnNotebookPageChanged' not implemented!")
        event.Skip()

# end of class ControlGUI

class OvenControlGUI(wx.App):
    def OnInit(self):
        self.frame = ControlGUI(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# end of class OvenControlGUI

if __name__ == "__main__":
    app = OvenControlGUI(0)
    app.MainLoop()
