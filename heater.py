#!/usr/bin/python
#-*- coding: latin-1 -*-

class Heater (object):
    """Class definition of a heater, an object that bundles heater 
    capabilities and setpoints
    """

    def __init__ (self, info, state, target, setpoint):
        """Define heater object and set basic properties.

        :param info: base information dictionary from configuration
        :param state: heater state ('a'ctive, 'o'ff, 'e'mergency or 'f'rozen)
        :param target: target temperature in celsius (float)
        :param setpoint: current setpoint temperature in celsius (float)
        """
        self.info = info
        self.state = state
        self.target = target
        self.setpoint = setpoint
