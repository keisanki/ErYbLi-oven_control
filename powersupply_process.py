#!/usr/bin/python
#-*- coding: latin-1 -*-

import time
import datetime
import multiprocessing
import Queue

import takasago

def powersupply_process (powersupplies, interval, currents, voltages, setpoints, queue):
    """Main function of the independent powersupplies process.

    This process is to query the powersupplies in regular intervals
    and to update the shared memory array accordingly.

    :param powersupplies: dictionary of powersupplies
    :param interval: Time interval in seconds between sensor updates
    :param currents: Shared memory array to hold current values
    :param voltages: Shared memory array to hold voltage values
    :param setpoints: Shared memory array to hold current setpoints
    :param queue: message queue for signalling purposes
    """
    timedelta_interval = datetime.timedelta (seconds = interval)

    # references so that we can later detect setpoint changes
    last_setpoints = []
    for value in setpoints:
        last_setpoints.append (value)

    referencetime = datetime.datetime.now ()
    while True:

        # update shared memory area with powersupply information
        now = datetime.datetime.now ()
        if now - referencetime > timedelta_interval:
            referencetime = now
            for psu in powersupplies:
                idx = powersupplies[psu].position
                # note: updating the array should internally be thread safe

                # current
                value = powersupplies[psu].getCurrent ()
                if value < -0.1:
                    # just to be sure, try again on failure
                    value = powersupplies[psu].getCurrent ()
                if value > -0.1:
                    currents[idx] = value
                else:
                    currents[idx] = -1.0

                # voltage
                value = powersupplies[psu].getVoltage ()
                if value < -0.1:
                    # just to be sure, try again on failure
                    value = powersupplies[psu].getVoltage ()
                if value > -0.1:
                    voltages[idx] = value
                else:
                    voltages[idx] = -1.0

        # check whether new powersupply setpoints are available
        for psu in powersupplies:
            idx = powersupplies[psu].position
            if setpoints[idx] != last_setpoints[idx]:
                powersupplies[psu].setCurrent (setpoints[idx])
                last_setpoints[idx] = setpoints[idx]

        # check whether there is a message from the parent process
        try:
            message = queue.get_nowait ()
            if message == 'q':
                # parent is about to quit
                return True
            if message.startswith ('on '):
                # turn on powersupply output
                powersupplies[message[3:]].setOutput (True)
            if message.startswith ('off '):
                # turn off powersupply output
                powersupplies[message[4:]].setOutput (False)
        except Queue.Empty:
            pass

        # wait a bit and get new timestamp
        time.sleep (0.100)
        now = datetime.datetime.now ()


    """End of while loop"""
