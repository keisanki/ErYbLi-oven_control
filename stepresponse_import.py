#!/usr/bin/python

import time
import datetime
import sys
import numpy
from scipy import optimize
from pylab import genfromtxt

from thermocouples_reference import thermocouples as tc_ref

import max31855
import takasago

################# Program settings (need to adjust) #####################

# number of thermocouple to use
sensor = 8
# thermocouple type
tc_type = 'C'
# name of serial device
device = '/dev/ttyAMA0'
#device = '/dev/ttyUSB0'
# address of powersupply to use
address = 1
# size of current step in A
stepsize = 0.3
# time between start of measurement and current step in s
steptime = 600
# duration of data acquisition after temperature step in s
duration = 7200
# time in s between individual temperature measurements
measure_interval = 1

############# Main program (normally no need to adjust) #################

def fitfunc (t, T0, k, tau, delay):
    """Fitting function to model the system response"""
    return T0 + numpy.heaviside (t - abs(delay), 0) * stepsize * k * (1 - numpy.exp (- (t-abs(delay))/tau))

def correctTemperature (temp_raw, temp_rj):
    """Recalibrate the raw MAX31855K value to the actual, nonlinear thermocouple."""
    coeff = 0.041276
    emf_tc = (temp_raw - temp_rj) * coeff # emf originally measured by MAX31855
    return tc_ref[tc_type].inverse_CmV (emf_tc, Tref = temp_rj)

def measure (verbose = False):
    """Acquire step response data from the system"""
    # setup
    cs_pins_all = [7, 8, 25, 24, 23, 18, 17, 5, 12, 13]
    cs_pins = [cs_pins_all[sensor-1]]
    clock_pin = 22
    data_pin = 27
    units = "c"

    thermocouples = []
    for cs_pin in cs_pins:
        thermocouples.append (max31855.MAX31855 (cs_pin, clock_pin, data_pin, units, type = "K"))
        cs_pins_all = filter (lambda pin: pin != cs_pin, cs_pins_all)

    thermocouples_inactive = []
    for cs_pin in cs_pins_all:
        thermocouples_inactive.append (max31855.MAX31855 (cs_pin, clock_pin, data_pin, units, type = "K"))

    psu = takasago.TakasagoPowersupply (device, address, max_current = 10)
    current = psu.getCurrent ()

    nowtime = datetime.datetime.now ()
    starttime = nowtime
    stoptime  = starttime + datetime.timedelta (seconds = duration + steptime)
    step_done = False

    xdata = []
    ydata = []

    # data acquisition
    running = True
    while running and nowtime < stoptime:
        nowtime = datetime.datetime.now ()
        deltatime = nowtime - starttime - datetime.timedelta (seconds = steptime)
        if deltatime >= datetime.timedelta (seconds = 0) and not step_done:
            psu.setCurrent (current + stepsize)
            step_done = True
        if verbose:
            sys.stdout.write ("{}\t{}\t".format (deltatime.total_seconds (), psu.getCurrent ()))
        try:
            for thermocouple in thermocouples:
                try:
                    tc = thermocouple.get_sensor_and_rj (ignore_errors = True)
                    Tcorrected = correctTemperature (tc['sensor'], tc['rj'])
                    xdata = numpy.append (xdata, deltatime.total_seconds ())
                    ydata = numpy.append (ydata, Tcorrected)
                    if verbose:
                        sys.stdout.write ("{}\t".format (Tcorrected))
                except max31855.MAX31855Error as e:
                    tc = "Error: "+ e.value
                    sys.stdout.write ("{}\t".format (tc))
            time.sleep(measure_interval)
        except KeyboardInterrupt:
            running = False
        if verbose:
            sys.stdout.write ("\n")
            sys.stdout.flush ()

    # reset powersupply to initial current
    psu.setCurrent (current)

    # cleanup operations
    for thermocouple in thermocouples:
        thermocouple.cleanup ()
    for thermocouple in thermocouples_inactive:
        thermocouple.cleanup ()

    return [xdata, ydata]

def importdata (filename):
    """Import the data from a previous run of the program"""
    mat = genfromtxt (filename)

    xdata = mat[:,0]
    ydata = mat[:,2]

    return [xdata, ydata]

def analysis (xdata, ydata, verbose = False):
    """Calculate optimal PID parameters from the given data"""
    # data fitting
    guessT0 = numpy.mean (ydata[1:50])
    guessk  = (numpy.mean (ydata[-50:-1]) - guessT0) / stepsize
    params, params_covariance = optimize.curve_fit (fitfunc, xdata, ydata, p0 = [guessT0, guessk, 1000, 100])

    T0, k, tau, delta = params
    delta = 100
    if verbose:
        print "\nFit result:"
        print "T0    = {:7.3f} degC".format (T0)
        print "k     = {:7.3f} degC/A".format (k)
        print "tau   = {:7.3f} s".format (tau)
        print "delta = {:7.3f} s".format (delta)

    # fit analysis (SIMC-PID tunings) for a cascade form PID controller
    Kc   = 0.5/k * tau/delta
    tauI = 8*delta
    tauD = 0

    # conversion into standard PID parameters
    gainP = Kc * (tauD + tauI)/tauI
    gainI = Kc / tauI
    gainD = Kc * tauD

    return [gainP, gainI, gainD]

if __name__ == "__main__":
    """Main program"""
    # measure new data
    #xdata, ydata = measure (verbose = True)

    # or import old data
    xdata, ydata = importdata ("/home/pi/stepresponse.dat")

    gainP, gainI, gainD = analysis (xdata, ydata, verbose = True)

    print "\nRecommended PID settings:"
    print "P = {:6.2f} mA/degC".format (1000 * gainP)
    print "I = {:6.2f} mA/(degC*s)".format (1000 * gainI)
    print "D = {:6.2f} mA/(degC/s)".format (1000 * gainD)
