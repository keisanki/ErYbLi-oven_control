#!/usr/bin/python
#-*- coding: latin-1 -*-
"""Module for importing and saving the ErYbLi-oven control configuration.

The configuration file is in Windows .ini style.
"""

from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError
import shutil

class Configuration (object):
    """Everything related to the configuration file"""

    def __init__ (self, config = 'ErYbLi-oven_control.ini'):
        """Create the Configuration object.

        :param config: (full) path to config file
                       (default: 'ErYbLi-oven_control.ini')
        """

        self.configfile = config

        self.__parser = SafeConfigParser ({
                                'db_id': None,
                                'db_id_I': None,
                                'db_id_P': None,
                                'max_delta_time': '1800',
                                'max_delta_temp': '5',
                                'max_delta_current': '0.2',
                                })
        #self.__parser = SafeConfigParser ()
        self.load ()

    def load (self):
        """Load the configuration file"""

        self.__parser.read (self.configfile)

    def write (self):
        """Write the configuration file after creating a .bak copy
        of the current one
        """

        shutil.copy2 (self.configfile, self.configfile + '.bak')

        with open (self.configfile, 'wb') as configfile:
            self.__parser.write (configfile)

    def getGeneral (self, option):
        """Get a single option from the general section

        :param option: string of option name to be retrieved
        :return: value of the option or None if not found
        """

        try:
            return self.__parser.get ('general', option)
        except NoSectionError:
            print "No general section found"
        except NoOptionError:
            print "Option '", option, "' not found in general configuration section"

        return None

    def updateGeneral (self, option, value):
        """Update a single option from the general section.
        For convenience the value is cast to str before set.

        :param option: string of option name to be updated
        :param value: new set value
        """

        return self.__parser.set ('general', option, str (value))

    def getDatabase (self, option):
        """Get a single option from the database section

        :param option: string of option name to be retrieved
        :return: value of the option or None if not found
        """

        try:
            return self.__parser.get ('database', option)
        except NoSectionError:
            print "No general section found"
        except NoOptionError:
            print "Option '", option, "' not found in general configuration section"

        return None

    def updateDatabase (self, option, value):
        """Update a single option from the database section.
        For convenience the value is cast to str before set.

        :param option: string of option name to be updated
        :param value: new set value
        """

        return self.__parser.set ('database', option, str (value))

    def getRecipients (self):
        """Get a list of all recipient e-mail addresses

        :return: list with all email addresses
        """

        recipients = self.__parser.items ('recipients')

        # need to start at position 6 here as for some reason the default
        # values of the ConfigParser get returned first
        return [val[1] for val in recipients[6:]]

    def setRecipients (self, recipients):
        """Set recipients from a list of e-mail addresses

        :param recipients: list of e-mail addresses
        """

        # remove old list of recipients
        oldrecipients = self.__parser.items ('recipients')
        for val in oldrecipients:
            self.__parser.remove_option ('recipients', val[0])

        # build up new list of recipients
        for num, address in enumerate (recipients, 1):
            self.__parser.set ('recipients', "name{}".format(num), address)

    def getOvenNames (self):
        """Get a list of all configured ovens.

        :return: list of all oven names
        """

        ovens = []
        for section in self.__parser.sections ():
            if section.startswith ('oven'):
                try:
                    ovens.append (self.__parser.get (section, 'name'))
                except NoOptionError:
                    print "Oven section does not contain a name"

        return ovens

    def getPowersupplyNames (self):
        """Get a list of all configured powersupplies.

        :return: list of all power supply names
        """

        powersupplies = []
        for section in self.__parser.sections ():
            if section.startswith ('powersupply'):
                try:
                    powersupplies.append (self.__parser.get (section, 'name'))
                except NoOptionError:
                    print "Powersupply section does not contain a name"

        return powersupplies

    def getThermocoupleNames (self):
        """Get a list of all configured thermocouples.

        :return: list of all thermocouple names
        """

        thermocouples = []
        for section in self.__parser.sections ():
            if section.startswith ('thermocouple'):
                try:
                    thermocouples.append (self.__parser.get (section, 'name'))
                except NoOptionError:
                    print "Thermocouple section does not contain a name"

        return thermocouples

    def getHeaterNames (self):
        """Get a list of all configured heaters

        :return: list of all heater names
        """

        heaters = []
        for section in self.__parser.sections ():
            if section.startswith ('heater'):
                try:
                    heaters.append (self.__parser.get (section, 'name'))
                except NoOptionError:
                    print "Heater section does not contain a name"

        return heaters

    def getOven (self, name):
        """Get all the information on a given oven.

        A typical oven section in the .ini file would be

        .. code::

            [oven Erbium]
            name = Erbium
            heater1 = Er oven bottom
            heater2 = Er oven top
            heater3 = Collimator

        ::

        The return dictionary contains the keys "name" and "heater", where
        "heater" contains a list of all heater entries.

        :param name: name string of oven (default: none)
        :return: oven data as dictionary or False if not found
        """

        for section in self.__parser.sections ():
            if (section.startswith ('oven')) and \
               (self.__parser.get (section, "name") == name):

                # compile a list of all necessary heaters
                heaters = []
                heater_items = self.__parser.items (section)
                for key, value in heater_items:
                    if (key.startswith ('heater')):
                        heaters.append (value)

                if len (heaters) == 0:
                    print "Oven does not define any heaters"
                    return False

                try:
                    info = {'name'    : self.__parser.get (section, 'name'),
                            'heaters' : heaters}
                except NoOptionError:
                    print "Oven section not complete"
                    return False

                return info

        return False

    def getPowersupply (self, name):
        """Get all the information on a given powersupply.

        A typical powersupply section in the .ini file would be

        .. code::

            [powersupply Er_bottom]
            name = Er oven bottom
            model = KX
            address = 1
            max_current = 10.0
            db_id_i = O3C1
            db_id_p = 03P1

        ::

        The keys in the returned dictionary match those of the .ini file.
        The 'db_id_i' and 'db_id_p' entries are optional, powersupplies without a
        database ID will not be logged to the database. Power information will
        only be logged if 'db_id_P' is provided.

        :param name: name string of the power supply (default: none)
        :return: power supply data as dictrionary or False if not found
        """

        for section in self.__parser.sections ():
            if (section.startswith ('powersupply')) and \
               (self.__parser.get (section, "name") == name):

                try:
                    info = {'name' : self.__parser.get (section, 'name'),
                            'model' : self.__parser.get (section, 'model'),
                            'address' : self.__parser.getint (section, 'address'),
                            'max_current' : self.__parser.getfloat (section, 'max_current'),
                            'db_id_i' : self.__parser.get (section, 'db_id_i'),
                            'db_id_p' : self.__parser.get (section, 'db_id_p')}
                except NoOptionError:
                    print "Powersupply section not complete"
                    return False

                return info

        return False

    def getThermocouple (self, name):
        """Get all the information on a given thermocouple sensor.

        A typical thermocouple section in the .ini file would be

        .. code::

            [thermocouple Er_bottom]
            name = Er oven bottom
            max_temp = 700
            type = C
            pin = 1
            db_id = O3T1

        ::

        The keys in the returned dictionary match those of the .ini file.
        The 'db_id' entry is optional, powersupplies without a database ID
        will not be logged to the database.

        :param name: name string of thermocouple (default: none)
        :return: thermocouple data as dictionary or False if not found
        """

        for section in self.__parser.sections ():
            if (section.startswith ('thermocouple')) and \
               (self.__parser.get (section, "name") == name):

                try:
                    info = {'name' : self.__parser.get (section, 'name'),
                            'max_temp' : self.__parser.getfloat (section, 'max_temp'),
                            'type' : self.__parser.get (section, 'type'),
                            'pin' : self.__parser.getint (section, 'pin'),
                            'db_id' : self.__parser.get (section, 'db_id')}
                except NoOptionError:
                    print "Thermocouple section not complete"
                    return False

                return info

        return False

    def getHeater (self, name):
        """Get all the information on a given heater.

        A typical heater section in the .ini file would be

        .. code::

            [heater Er_bottom]
            name = Er oven bottom
            powersupply = Er oven bottom
            thermocouple = Er oven bottom
            temp_low = 500
            temp_high = 1100
            ramp_speed = 10
            pid_p = 1000
            pid_i = 30
            pid_d = 5

        ::

        The keys in the returned dictionary match those of the .ini file.

        :param name: name string of heater (default: none)
        :return: heater data as dictionary or False if not found
        """

        for section in self.__parser.sections ():
            if (section.startswith ('heater')) and \
               (self.__parser.get (section, "name") == name):

                try:
                    info = {'name' : self.__parser.get (section, 'name'),
                            'powersupply' : self.__parser.get (section, 'powersupply'),
                            'thermocouple' : self.__parser.get (section, 'thermocouple'),
                            'temp_low' : self.__parser.getfloat (section, 'temp_low'),
                            'temp_high' : self.__parser.getfloat (section, 'temp_high'),
                            'ramp_speed' : self.__parser.getfloat (section, 'ramp_speed'),
                            'emergency_ramp_speed' : self.__parser.getfloat (section, 'emergency_ramp_speed'),
                            'low_pid_p' : self.__parser.getfloat (section, 'low_pid_p'),
                            'low_pid_i' : self.__parser.getfloat (section, 'low_pid_i'),
                            'low_pid_d' : self.__parser.getfloat (section, 'low_pid_d'),
                            'high_pid_p' : self.__parser.getfloat (section, 'high_pid_p'),
                            'high_pid_i' : self.__parser.getfloat (section, 'high_pid_i'),
                            'high_pid_d' : self.__parser.getfloat (section, 'high_pid_d')}
                except NoOptionError:
                    print "Heater section not complete"
                    return False

                return info

        return False

    def updateHeaterVal (self, name, key, value):
        """Updates the low and high temperature of a given heater

        :param name: name string of heater (default: none)
        :param key: string of configuration key (default: none)
        :param value: configuration value (will be cast to string, default: none)
        """
        for section in self.__parser.sections ():
            if (section.startswith ('heater')) and \
               (self.__parser.get (section, "name") == name):
                 self.__parser.set (section, key, str (value))

    def getUPSInfo (self):
        """Get a list of all UPS IPs

        :return: list of UPS IPs
        """

        IPs = self.__parser.items ('UPS')

        # need to start at position 6 here as for some reason the default
        # values of the ConfigParser get returned first
        return [val[1] for val in IPs[6:]]


if __name__ == '__main__':
    """Just testing"""
    cfg = Configuration ()
    cfg.load ()
#    print cfg.getPowersupply ("Er oven bottom")
#    print cfg.getThermocouple ("Er oven bottom")
#    print cfg.getPowersupplyNames ()
#    print cfg.getThermocoupleNames ()
#    print cfg.getHeaterNames ()
#    print cfg.getOvenNames ()
#    print cfg.getOven ("Erbium")
#    print cfg.getHeater ("Er oven bottom")
#    print cfg.getHeater("Er oven bottom")
#    cfg.updateHeaterTemp ("Er oven bottom", 600, 1000)
#    print cfg.getHeater("Resistance heater")
#    cfg.updateHeaterTemp ("Er oven bottom", temp_high = 800)
#    print cfg.getHeater("Er oven bottom")
#    print cfg.getRecipients ()
#    cfg.setRecipients (["addr1", "addr2", "addr3"])
    print cfg.getRecipients ()
#    cfg.write ()
#    print cfg.getGeneral ('thermocouple_polling_interval')
#    print cfg.getThermocouple ('Dummy sensor')
#    print cfg.getDatabase ('host')
#    print cfg.getDatabase ('max_delta_time')
