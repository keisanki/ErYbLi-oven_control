Raspberry Pi GPIO wiring scheme
===============================

  Raspberry Pi        |  Cable   |  Board
Pin Nr | Pin name     | Wire Nr. | Function
-------+--------------+----------+--------------------------------------------------
   1   | 3.3 V        |     2    | MAX31855 and ADM3252EEBZ power supply
   2   | 5 V          |          | (LCD power supply)
   3   | BCM 2        |          | 
   4   | 5 V          |    15    | 5 V for buzzer (through buzzer to NPN collector)
   5   | BCM 3        |          | 
   6   | GND          |          | 
   7   | BCM 4        |    14    | Buzzer signal (NPN base via 1 kOhm)
   8   | BCM 14 / TXD |    12    | ADM3252EEBZ TIN1
   9   | GND          |          | 
  10   | BCM 15 / RXD |    13    | ADM3252EEBZ TOUT1
  11   | BCM 17       |     5    | MAX31855 SS (7)
  12   | BCM 18       |     6    | MAX31855 SS (6)
  13   | BCM 27       |     4    | MAX31855 MISO
  14   | GND          |     1    | GND for MAX31855, ADM3252EEBZ and NPN emitter
  15   | BCM 22       |     3    | MAX31855 SCK
  16   | BCM 23       |     7    | MAX31855 SS (5)
  17   | 3.3 V        |          | 
  18   | BCM 24       |     8    | MAX31855 SS (4)
  19   | BCM 10       |          | 
  20   | GND          |          | 
  21   | BCM 9        |          | 
  22   | BCM 25       |     9    | MAX31855 SS (3)
  23   | BCM 11       |          | 
  24   | BCM 8        |    10    | MAX31855 SS (2)
  25   | GND          |          | 
  26   | BCM 7        |    11    | MAX31855 SS (1)
  27   | BCM 0        |          | 
  28   | BCM 1        |          | 
  29   | BCM 5        |    17    | MAX31855 SS (8, external 6-pin)
  30   | GND          |          | 
  31   | BCM 6        |    16    | Water interlock switch (against ground)
  32   | BCM 12       |    18    | MAX31855 SS (9, external 6-pin)
  33   | BCM 13       |    19    | MAX31855 SS (10, external 4-pin)
  34   | GND          |          | 
  35   | BCM 19       |          | 
  36   | BCM 16       |          | 
  37   | BCM 26       |          | 
  38   | BCM 20       |          | 
  39   | GND          |          | 
  40   | BCM 21       |          | 

Currently 19 wires are used.
In total 24 wires are available.



Thermocouple readout board
==========================

A MAX31855PMB1 peripheral module is used. This module uses a linear
calibration for K type thermocouples. In the control program the reported
temperature is converted by to a junction voltage using 41.276 uV/°C and then
converted to the proper temperature (also for other thermocouple types) using
the python thermocouples_reference library that is based on NIST data.

The module board connector has 6 pins:
1 - SS   - chip select line
2 - N.C. - not connected
3 - MISO - data output
4 - SCK  - clock input
5 - GND  - ground
6 - VCC  - 3.3 V power supply

Lines 3, 4, 5, 6 are shared among all readout boards.
The chip select line 1 is seaparate for each sensor.

Connection to external MAX31855PMB1 boards via Hirose connectors:

6-pin connector, HR10A-7R-6S(73), for two sensors
  pin 1: SS for first MAX31855PMB1
  pin 2: SS for second MAX31855PMB1
  pin 3: MISO
  pin 4: SCK
  pin 5: GND
  pin 6: VCC

4-pin connector, HR10A-7R-4P(73), for single sensor
  pin 1: SS
  pin 2: MISO
  pin 3: SCK
  pin 4: VCC
  GND  : GND



Raspberry Pi serial port
========================

For the serial port working on BCM 14 & 15 the following changes are necessary:
- Both GPIO must be set to ALT0 mode iwth the "gpio" command. This command
  seems to use the wiring Pi number scheme.
      > gpio mode 15 ALT0
      > gpio mode 16 ALT0
- Need to remove the serial terminal from this serial port. This can be done
  with the "sudo raspi-config" command. There, select
      - 5 Interfacing Options  (Configure connections to peripherals)
      - P6 Serial (Enable/Disable shell and kernel messages on the serial connection)
      - <No> (To disable serial console)
- Need to disable bluetooth as the Raspberry Pi is using the serial interface
  to communicate with the bluetooth chip. To do so include in /boot/config.txt
      dtoverlay=pi3-disable-bt
- That should be everything. The serial port is then called /dev/ttyAMA0.



MAX3232 level shifter for serial port (not in active use)
=========================================================

The Raspberry Pi GPIO ports work at 3.3 V. The RS232 protocal uses higher
voltages and a level shifter becomes necessary. I decided to use the MAX3232
level shifter. Connections are as by the manual.

data lines
----------
pin 11: TXD input from Raspberry Pi
pin 12: RXD output to Raspberry Pi
pin 13: RXD input from RS232 (D-SUB 9 connector pin 2)
pin 14: TXD output to RS232  (D-SUB 9 connector pin 3)

power supply
------------
pin 15: GND (connects also to D-SUB 9 connector pin 5)
pin 16: +3.3 V from Raspberry Pi

capacitors
----------
pin  1 - pin 3: 0.1 uF capacitor
pin  4 - pin 5: 0.1 uF capacitor
pin  2 - GND  : 0.1 uF capacitor
pin  6 - GND  : 0.1 uF capacitor
pin 16 - GND  : 0.1 uF capacitor



ADM3252 isolated level shifter for serial port
==============================================

It turned out that the MAX2323, while working, introduced some noise and
general level shifts in the thermocouple sensor readings. As an alternative
now an galvanically isolated level shifter is used, the EVAL-ADM3252EEBZ
evaluation board where everything is already integrated. Connections are

data lines
----------
TIN1 : TXD input from Raspberry Pi (was MAX2323 pin 11)
TOUT1: TXD output to RS232 (D-SUB connector pin 3)
ROUT1: RDX output to Raspberry Pi (was MAX2323 pin 12)
RIN1 : RDX input from RS232 (D-SUB connector pin 2)


power supply
------------
VCC: +3.3 V from Raspberry Pi
GND: GND from Raspberry Pi
ISOGND: isolated GND to RS232 (D-SUB connector pin 5)



Florian Schaefer, 2018/08/24
