#!/usr/bin/python
#-*- coding: latin-1 -*-
"""Logging of oven data to the central MySQL database"""

import time
import atexit
import MySQLdb as mdb

class DataLogger (object):
    """Data logging object to write temperature and powersupply data to a
    database (MySQL driven in this case)"""

    def __init__ (self, config, temperatures, currents, voltages):
        """Initialization of the database logger.

        :param config: global program configuration dictionary (default: none)
        :param temperatures: shared memory array of temperatures (default: none)
        :param currents: shared memory array of currents (default: none)
        :param voltages: shared memory array of voltages (default: none)
        """
        self.host = config.getDatabase ('host')
        self.db = config.getDatabase ('db')
        self.user = config.getDatabase ('user')
        self.passwd = config.getDatabase ('passwd')
        self.con = None
        self.cursor = None

        self.config = config
        self.temperatures = temperatures
        self.currents = currents
        self.voltages = voltages

        self.last_temperatures = [-1] * len (self.temperatures)
        self.last_currents = [-1] * len (self.currents)
        self.times_temperatures = [-1] * len (self.temperatures)
        self.times_currents = [-1] * len (self.currents)

        atexit.register (self.cleanup)

    def cleanup (self):
        """Close the DB connection at the end of the program"""
        try:
            self.closeConnection ()
        except:
            pass

    def openConnection (self):
        """Open a connection to the MySQL server and prepares the cursor"""
        self.con = mdb.connect (
                                host = self.host,
                                db = self.db,
                                user = self.user,
                                passwd = self.passwd,
                                connect_timeout = 3
                               )
        self.cursor = self.con.cursor ()

    def closeConnection (self):
        """Close the DB connection"""
        self.con.close ()
        self.cursur = None
        self.con = None

    def insertValue (self, key, value):
        """Generic function to insert a (id, value) pair into the log_data table

        :param key: identifier of the value (string, default: none)
        :param value: value to be logges (float, default: none)
        """
        sql = "INSERT INTO log_data (`id`, `value`) VALUES ('{}', '{}')".format(key, value)
        #print sql
        try:
            self.cursor.execute (sql)
            self.con.commit ()
        except mdb.OperationalError as e:
            #TODO: react only to SQL exceptions and raise them again
            self.con.rollback ()
            raise e

    def updateLogs (self, e = None):
        """Insert current temperatures, currents and powers into database, if
        and only if the last log values are (i) too old or (ii) have changed by
        too much.
        """
        #TODO: Add exceptions in case openConnection fails

        delta_time = float (self.config.getDatabase ('max_delta_time'))
        delta_temp = float (self.config.getDatabase ('max_delta_temp'))
        delta_current = float (self.config.getDatabase ('max_delta_current'))

        try:
            now = time.time ()
            for pos, tc in enumerate (self.config.getThermocoupleNames ()):
                db_id = self.config.getThermocouple(tc)['db_id']
                if not db_id:
                    # no database ID specified -> no logging of this part
                    continue
                temp = self.temperatures[pos]
                # log every, e.g. 30, minutes or for temperature changes above, e.g. 5°C
                if (now - self.times_temperatures[pos] > delta_time) or \
                   (abs (self.last_temperatures[pos] - temp) > delta_temp):
                       if temp > 0:
                           # only update with valid temperatures
                           if not self.con:
                               self.openConnection ()
                           self.insertValue (db_id, temp)
                           #print "intert into db for '{}': {}".format (db_id, temp)
                           self.times_temperatures[pos] = now
                           self.last_temperatures[pos] = temp

            for pos, psu in enumerate (self.config.getPowersupplyNames ()):
                db_id_i = self.config.getPowersupply(psu)['db_id_i']
                db_id_p = self.config.getPowersupply(psu)['db_id_p']
                if not db_id_i:
                    # no database ID specified -> no logging of this part
                    continue
                current = self.currents[pos]
                voltage = self.voltages[pos]
                # log every, e.g. 30, minutes or for current changes above, e.g. 0.2 A
                # also: log power (if requested) in sync and based on current log
                if (now - self.times_currents[pos] > delta_time) or \
                   (abs (self.last_currents[pos] - current) > delta_current):
                       if current >= -0.1:
                           # current logging: only update with valid currents
                           if not self.con:
                               self.openConnection ()
                           self.insertValue (db_id_i, current)
                           #print "intert into db for '{}': {}".format (db_id_i, current)
                           self.times_currents[pos] = now
                           self.last_currents[pos] = current
                       if current >= -0.1 and voltage >= -0.1:
                           # power logging only update with valid current and voltage
                           if not self.con:
                               self.openConnection ()
                           self.insertValue (db_id_p, current*voltage)
                           #print "intert into db for '{}': {}".format (db_id_p, current*voltage)

            if self.con:
                self.closeConnection ()
            return True
        except mdb.OperationalError as e:
            return e


if __name__ == '__main__':
    """Just testing"""
    #logger = DataLogger ()
    #logger.openConnection ()
    #logger.insertValue ('TEST', '42')
