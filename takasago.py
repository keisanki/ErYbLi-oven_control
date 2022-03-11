#!/usr/bin/python
#-*- coding: latin-1 -*-
"""Module to interface to a Takagaso EX style power supply via serial interface.

For the ZX-S-400L power supply one needs to put it into EX compatibility mode.
This is done by putting function setting 61 to 1. Also note that the device 
address is registered in function setting register 60.
"""

import serial

class TakasagoPowersupply (object):
    """Handle basic output set and query operations of Takasago power supplies"""

    def __init__ (self, device = '/dev/ttyAMA0', address = 1, max_current = 1., model = "ZX", position = None):
        """Create and initialize the TakasagoPowersupply object.

        :param device: path to serical device (default: /dev/ttyUSB0)
        :param address: bus address of the powersupply (default: 1)
        :param max_current: maximum allowable current in A (default: 1.0)
        :param model: powersupply model, "ZX" or "KX" (default: "ZX")
        :param position: parameter to determine the position of the powersupply
                in a list (integer, default: None)
        """

        self.address = address
        self.max_current = max_current
        self.device = device
        self.model = model
        self.position = position

        self.serial = serial.Serial (
                        port     = self.device,
                        baudrate = 9600,
                        parity   = serial.PARITY_NONE,
                        stopbits = serial.STOPBITS_ONE,
                        bytesize = serial.EIGHTBITS,
                        timeout  = 0.5
                        )

        if model == "ZX":
            self.commands = {
                    "GetCurrent": "TK5",
                    "SetCurrent": "MC",
                    "GetVoltage": "TK4",
                    "SetVoltage": "MV",
                    "SetOutput": "OT"
                    }
        if model == "KX":
            self.commands = {
                    "GetCurrent": "TK7",
                    "SetCurrent": "OC",
                    "GetVoltage": "TK6",
                    "SetVoltage": "OV",
                    "SetOutput": "OT"
                    }

    def _sendCommand (self, address, cmd):
        """Low level function to send a command to a specific device

        :param address: power supply address
        :param cmd: command string to be sent
        """
        self.serial.flushInput ()
        self.serial.flushOutput ()

        self.serial.write ("A" + str(address) + "," + cmd + "\r")
        self.serial.flush ()

    def _readReply (self):
        """Read a reply string from the serial bus

        :return: single line reply strong or None if timeout
        """
        resp = ''
        while True:
            char = self.serial.read ()
            if char == '\r':
                break
            if len (char):
                resp += char
            else:
                # We had a timeout
                #print "timeout when waiting for Takasago response"
                return None

        return resp

    def setOutput (self, state):
        """Enables/Disable the output of the powersupply.

        :param state: boolean parameter indicating the state (True = On, False = Off)
        :return: True on success
        """
        try:
            if state:
                self._sendCommand (self.address, self.commands["SetOutput"] + "1")
            else:
                self._sendCommand (self.address, self.commands["SetOutput"] + "0")
        except:
            return False

        return True

    def setCurrent (self, current):
        """Set the powersupply current, clipping to the max_current

        :param current: set current in A
        :return: True on success
        """
        if (current > self.max_current):
            current = self.max_current
        if (current < 0):
            current = 0

        try:
            self._sendCommand (self.address, self.commands["SetCurrent"] + str(current))
        except:
            return False

        return True

    def getCurrent (self):
        """Query the actual current of the powersupply

        :return: current in A or None if not successful
        """
        try:
            self._sendCommand (self.address, self.commands["GetCurrent"])
            reply = self._readReply ()
            return float (reply[0:-1])
        except:
            return None

        return None

    def setVoltage (self, voltage):
        """Set the powersupply voltage

        :param current: set voltage in V
        :return: True on success
        """
        if voltage < 0:
            voltage = 0

        try:
            self._sendCommand (self.address, self.commands["SetVoltage"] + str(voltage))
        except:
            return False

        return True

    def getVoltage (self):
        """Query the actual voltage of the powersupply

        :return: voltage in V or None if not successful
        """
        try:
            self._sendCommand (self.address, self.commands["GetVoltage"])
            reply = self._readReply ()
            return float (reply[0:-1])
        except:
            return None

        return None

    def close (self):
        """Close serial connection"""

        self.serial.close ()


if __name__ == '__main__':
    """Just testing"""
    psu = TakasagoPowersupply (address = 3, model = "KX")
    #psu.setOutput (True)
    #psu.setCurrent (0.3)
    print psu.getVoltage ()
    print psu.getCurrent ()
    #psu.setOutput (False)
    psu.close ()
