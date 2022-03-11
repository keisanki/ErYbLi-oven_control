#!/usr/bin/python
#-*- coding: latin-1 -*-

import time
import datetime
import multiprocessing
import Queue
import numpy
from numbers import Number

import thermocouple

def calc_clean_mean_temp (temperatures, threshold):
    """Function to calculate mean temperatures discarding outliers.

    :param temperatures: list of temperature values
    :param threshold: temperature is discarded if farther away than threshold from the median
    :return: cleaned up mean value if more than 3 elements, -1 if no elements and mean value otherwise
    """

    if len (temperatures) == 0:
        # empty list
        return -1;

    if len (temperatures) < 4:
        # too few elements for outlier analysis
        return numpy.mean (temperatures)

    # create a new list with the outliers removed
    median_temp = numpy.median (temperatures)
    valid_temperatures = [T for T in temperatures if abs (T - median_temp) < threshold]

    # debugging
    #bad_temperatures = [T for T in temperatures if abs (T - median_temp) >= threshold]
    #if len (bad_temperatures):
    #    print "discarded temperatures {} where meadian is {}".format(bad_temperatures, median_temp)

    # return mean value of that new list
    return numpy.mean (valid_temperatures)

def thermocouples_update (thermocouples, avg):
    """This function does the heavy work of
    - reading all thermocouples for avg number of times
    - averaging over successful reads
    - converting each value into the proper scale

    We iterate on purpose first over each thermocouple and then do the
    repetitions. This is to give each therocouple a bit of time so that the
    ADC might decide on a different value.

    :param thermocouples: dictionary of thermocouples to process
    :param avg: averaging to use
    """
    # prepare date structures
    temperatures = {}
    junction_temperatures = {}
    for name,tc in thermocouples.items ():
        # tc readings
        temperatures[name] = []
        # rj (refence junction) readings
        junction_temperatures[name] = []

    # read all data
    temptry = 0
    #starttime = datetime.datetime.now ()
    for i in xrange (avg):
        for name,tc in thermocouples.items ():
            temptry = tc.updateBothTemperatures ()
            if temptry == None:
                continue
            if temptry['sensor'] > 0:
                temperatures[name].append (temptry['sensor'])
            if temptry['rj'] > 0:
                junction_temperatures[name].append (temptry['rj'])
        time.sleep (0.05)
    #print "read done, needed {}".format(datetime.datetime.now()-starttime)

    # average over successful reads
    mean_temperatures = {}
    mean_junction_temperatures = {}
    for name in thermocouples.keys ():
        mean_temperatures[name] = calc_clean_mean_temp (temperatures[name], 2.)
        mean_junction_temperatures[name] = calc_clean_mean_temp (junction_temperatures[name], 2.)

    # do temperature correction
    for name,tc in thermocouples.items ():
        if mean_temperatures[name] > 0 and mean_junction_temperatures[name] > 0:
            # everything is fine and we can calculate the corrected temperature
            tc.temperature = tc.correctTemperature (mean_temperatures[name], mean_junction_temperatures[name])
        else:
            # failed to read thermocouple temperature -> sensor failed
            tc.temperature = -1

def thermocouple_process (thermocouples, interval, avg, shmem, queue):
    """Main function of the independent thermocouple process.

    This process is to query the thermocouples in regular intervals
    and to update the shared memory temperature array accordingly

    :param thermocouples: dictionary of thermocouples
    :param interval: Time interval in seconds between sensor updates
    :param avg: number of averages to take for each update
    :param shmem: Shared memory array to hold temperature values
    :param queue: message queue for signalling purposes
    """
    thermocouples_update (thermocouples, avg)
    referencetime = datetime.datetime.now ()
    smoothing_factor = 1.
    while True:

        # wait for specified time between udpates
        now = datetime.datetime.now ()
        while now - referencetime < datetime.timedelta (seconds = interval):
            # check whether there is a message from the parent process
            try:
                message = queue.get_nowait ()
                if message == 'q':
                    # note: don't need to call thermocouple.cleanup due to the atexit module
                    return True
                if isinstance (message, Number):
                    # update smoothing factor to be effective over given range of samples
                    smoothing_factor = message
                    #print "received new smoothing factor {}".format(smoothing_factor)
            except Queue.Empty:
                pass

            # wait a bit and get new timestamp
            time.sleep (0.100)
            now = datetime.datetime.now ()
        referencetime = now

        # run the thermocouple update
        thermocouples_update (thermocouples, avg)

        # update shared memory area
        for sensor in thermocouples:
            # Optional temperature smoothing 
            # (https://en.wikipedia.org/wiki/Exponential_smoothing)
            previoustemp = shmem[thermocouples[sensor].position]
            currenttemp  = thermocouples[sensor].temperature
            if thermocouples[sensor].temperature != -1:
                # smoothing
                newtemperature = smoothing_factor * currenttemp + (1-smoothing_factor) * previoustemp
            else:
                # no smoothing as previous value is probably not a valid temperature
                newtemperature = currenttemp

            # note: updating the array should internally be thread safe
            shmem[thermocouples[sensor].position] = newtemperature

    """End of while loop"""
