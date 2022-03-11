#!/usr/bin/python
#-*- coding: latin-1 -*-

from thermocouples_reference import thermocouples as tc_ref
import atexit

import max31855

class Thermocouple (object):
    """This class is the complete management of a single thermocouple.
    This includes reading the data from the MAX31855PMB chip and (if necessary)
    converting the data to the proper thermocouple type. Currently type K and C
    are supported.
    """

    def __init__ (self, type = 'K', pin = None, position = None):
        """Initialize a new thermocouple object.

        :param type: thermocouple type (either 'K' or 'C', default: 'K')
        :param pin: GPIO pin of the Raspberry Pi the corresponding MAX31855PMB
                sensor board is connected to (integer, default: None)
        :param position: optional parameter to fix the position of the thermocouple
                in a list (integer, default: None)
                Note: Initial temperature reading upon object initialization is not
                      performed if position parameter is not given.
        """

        self.type = type
        self.pin = pin
        self.temperature = -1.
        self.junctiontemp = -1.
        self.position = position
        atexit.register (self.cleanup)

        self.max31855 = max31855.MAX31855 (self.pin, 22, 27, type = self.type)
        if position:
            self.updateTemperature ()

    def updateTemperature (self):
        """Readout the MAX31855PMB board and update temperature variable of the sensor

        :return: temperature on success, None on error
        """

        temptry = None
        try:
            temptry = self.max31855.get ()
        except max31855.MAX31855Error:# as e:
            #print "thermocouple error: " + e.value
            return None

        self.temperature = temptry
        return self.temperature

    def updateJunctionTemperature (self):
        """Readout the MAX31855PMB board and update reference junction temperature
        variable of the sensor

        :return: reference temperature on success, None on error
        """

        temptry = None
        try:
            temptry = self.max31855.get_rj ()
        except max31855.MAX31855Error:# as e:
            #print "thermocouple error: " + e.value
            return None

        self.junctiontemp = temptry
        return self.junctiontemp

    def updateBothTemperatures (self):
        """Readout the MAX31855PMB board and update in a single query both the
        sensor and reference junction temperature

        :return: dictionary with keys 'sensor' and 'rj' on success, None on error
        """

        temptry = None
        try:
            temptry = self.max31855.get_sensor_and_rj (ignore_errors = True)
        except max31855.MAX31855Error:# as e:
            #print "thermocouple error: " + e.value
            return None

        # poor man's error detection
        if temptry['sensor'] > 2000.:
            return None
        if temptry['sensor'] == 0. and temptry['rj'] == 0.:
            return None

        self.temperature = temptry['sensor']
        self.junctiontemp = temptry['rj']
        return temptry

    def getTemperature (self):
        """Return the currently stored temperature"""

        return self.temperature

    def getJunctionTemperature (self):
        """Return the currently stored reference junction temperature"""

        return self.junctiontemp

    def correctTemperature (self, temp_raw, temp_rj):
        """Convenience function to recalibrate the raw MAX31855K value
        to the actual, nonlinear thermocouple.

        :param temp_raw: raw temperature in degC as from MAX31855K
        :param temp_rj: temperature in degC of the reference junction
        :return: corrected temperature in degC
        """
        coeff = 0.041276
        emf_tc = (temp_raw - temp_rj) * coeff # emf originally measured by MAX31855
        try:
            corrected_temp = tc_ref[self.type].inverse_CmV (emf_tc, Tref = temp_rj)
            #if self.type == 'C':
            #    print "raw temp: {}, rj temp: {}, emf: {}, corrected temp: {}".format (temp_raw, temp_rj, emf_tc, corrected_temp)
        except ValueError:
            corrected_temp = -1

        return corrected_temp

    def cleanup (self):
        """Do necessary cleanup operations at end of program.
        For the MAX31855K this means freeing the GPIO lines.
        """
        self.max31855.cleanup ()


if __name__ == '__main__':
    """Just testing"""
    tc = Thermocouple (type = 'K', pin = 22)
    tc.updateTemperature ()
    print tc.getTemperature ()
