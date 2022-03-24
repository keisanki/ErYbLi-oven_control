# ErYbLi-oven_control

This is the oven control program used in the ErYbLi experiment of the Quantum
Optics Group at Kyoto University.

It is intended to run on a Raspberry Pi with the corresponding Raspberry Pi
touchscreen installed. Additional technical details on the hardware
implementation can be found in the `README.txt` file.

ErYbLi-oven_control is built using Python and wxWidgets.

## Feature overview

Normal interaction with the program is through a full-screen graphical user
interface. This interface is divided into five sections that are represented as
separate notebook tabs and that can be displayed as necessary. We will take a
look at the different tabs now.

### The main control page

![ErYbLi-oven_control main control page](images/ErYbLi_oven_control.png)

In the **Oven selection** area the available ovens are listed as buttons.
Selected ovens are displayed in green and it is those ovens that will be
brought to their operating (that is high) temperatures. The operation mode of
the program is selected in the **Action selection** area. Here, the various
temperatures ramps for the selected ovens can be selected. Currently active
ramps are in yellow, once the target temperatures have been reached the button
turns green. Finally, the **Oven status** area displays the status of the
interlock system and, if applicable, the remaining time for the current ramp to
finish. The interlock system monitors the status of the cooling water flow, the
temperatures of all thermocouples, the resistances of all heating elements, the
status of all power supplies, and the information coming from one or more UPS
systems. Good interlocks are green, disabled interlocks are gray and failed
interlocks are red. A failed interlock triggers an emergency ramp of all ovens
to OFF.

### The monitor page

![ErYbLi-oven_control monitor page](images/ErYbLi_oven_monitor_TW.png)

This page informs in the **Oven temperatures** area graphically and numerically
on the current actual oven temperatures and their set values. The **Power
supplies** area provides similar information on all power supplies. Clicking on
the temperature graph toggles between a plot of the temperatures and a plot of
the temperature errors. Correspondingly, clicking the power supply graph
switches between power and current information. Unneeded information can be
removed from the plots by clicking on the corresponding row of the left side
table.

### The heater settings page

![ErYbLi-oven_control heater settings page](images/ErYbLi_oven_heater.png)

This tab allows for each heater to quickly modify the low and high temperature
setpoints, the parameters of the PID control loop and the ramping speeds.
Additional information on the associated power supplies and the maximum
allowable temperature is also shown. As that information, however, is very
relevant to the secure operation of the oven system it cannot be modified
through the graphical user interface. Instead, the configuration file needs to
be adjusted manually.

### The general settings page

![ErYbLi-oven_control settings page](images/ErYbLi_oven_settings.png)

This page exposes some of the most fundamental settings of the program, such as
the mail recipients for status messages and some options on the monitor plots
and the database logging facility. For a complete control of the program
settings, however, it is necessary to manually edit the configuration file.

### The automatic startup page

![ErYbLi-oven_control startup page](images/ErYbLi_oven_startup.png)

To help with operating the oven at inconvenient times, the program includes the
possibility a execute the actions from the main control page also via a timer
mechanism. This allows, e.g. to start warming up the oven at a very early time
in the morning and to have everything up and running by the time the crew
arrives in the laboratory.

## Contact

For any comments and/or bug reports please report to the author,
test@testdomain.jp.
