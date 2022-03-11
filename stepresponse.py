#!/usr/bin/python

import time
import datetime
import sys
import numpy
import argparse
from scipy import optimize
from pylab import genfromtxt

from thermocouples_reference import thermocouples as tc_ref

import max31855
import takasago

################# Program settings (might be adjusted) #####################

# all options can also be adjusted via the command line parameters

# number of thermocouple to use
sensor = 8 # Er top
# thermocouple type
tc_type = 'C'
# name of serial device
device = '/dev/ttyAMA0'
# address of powersupply to use
address = 1 # Er top
# size of current step in A
stepsize = 0.3
# time between start of measurement and current step in s
steptime = 600
# duration of data acquisition after temperature step in s
duration = 1800
# time in s between individual temperature measurements
measure_interval = 1

############# Main program (normally no need to adjust) #################



def fitfunc (t, T0, k, tau, delay):
    """Fitting function to model the system response"""
    return T0 + numpy.heaviside (t - numpy.abs(delay), 0) * args.stepsize * k * (1 - numpy.exp (- (t-numpy.abs(delay))/tau))

def correctTemperature (temp_raw, temp_rj):
    """Recalibrate the raw MAX31855K value to the actual, nonlinear thermocouple."""
    coeff = 0.041276
    emf_tc = (temp_raw - temp_rj) * coeff # emf originally measured by MAX31855
    return tc_ref[args.sensor_type].inverse_CmV (emf_tc, Tref = temp_rj)

def measure (verbose = False):
    """Acquire step response data from the system"""
    # setup
    cs_pins_all = [7, 8, 25, 24, 23, 18, 17, 5, 12, 13]
    cs_pins = [cs_pins_all[args.sensor_number-1]]
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

    psu = takasago.TakasagoPowersupply (args.device, args.address, max_current = 12)
    current = psu.getCurrent ()

    nowtime = datetime.datetime.now ()
    starttime = nowtime
    stoptime  = starttime + datetime.timedelta (seconds = args.duration + args.steptime)
    step_done = False

    xdata = []
    ydata = []

    # data acquisition
    running = True
    while running and nowtime < stoptime:
        nowtime = datetime.datetime.now ()
        deltatime = nowtime - starttime - datetime.timedelta (seconds = args.steptime)
        if deltatime >= datetime.timedelta (seconds = 0) and not step_done:
            psu.setCurrent (current + stepsize)
            step_done = True
        if verbose:
            sys.stdout.write ("{}\t{}\t".format (deltatime.total_seconds (), psu.getCurrent ()))
        if args.output_file:
            args.output_file.write ("{}\t{}\t".format (deltatime.total_seconds (), psu.getCurrent ()))
        try:
            for thermocouple in thermocouples:
                try:
                    tc = thermocouple.get_sensor_and_rj (ignore_errors = True)
                    Tcorrected = correctTemperature (tc['sensor'], tc['rj'])
                    xdata = numpy.append (xdata, deltatime.total_seconds ())
                    ydata = numpy.append (ydata, Tcorrected)
                    if verbose:
                        sys.stdout.write ("{}\n".format (Tcorrected))
                    if args.output_file:
                        args.output_file.write ("{}\n".format (Tcorrected))
                except max31855.MAX31855Error as e:
                    tc = "Error: "+ e.value
                    sys.stdout.write ("{}\n".format (tc))
            time.sleep(args.measure_interval)
        except KeyboardInterrupt:
            running = False
        if verbose:
            sys.stdout.flush ()
        if args.output_file:
            args.output_file.flush ()

    # reset powersupply to initial current
    psu.setCurrent (current)
    if verbose:
        sys.stdout.write ("Reset power supply to {} A\n".format(current))

    # cleanup operations
    for thermocouple in thermocouples:
        thermocouple.cleanup ()
    for thermocouple in thermocouples_inactive:
        thermocouple.cleanup ()

    if args.output_file:
        args.output_file.close ()

    return [xdata, ydata]

def importdata (filename):
    """Import the data from a previous run of the program"""
    mat = genfromtxt (filename)

    xdata = mat[:,0]
    ydata = mat[:,2]

    return [xdata, ydata]

def analysis (xdata, ydata, timeconst = 2., verbose = False):
    """Calculate optimal PID parameters from the given data"""
    # data fitting
    guessT0 = numpy.mean (ydata[1:50])
    guessk  = (numpy.mean (ydata[-50:-1]) - guessT0) / stepsize
    params, params_covariance = optimize.curve_fit (fitfunc, xdata, ydata, p0 = [guessT0, guessk, 500, 5])

    T0, k, tau, delta = params
    if verbose:
        print "\nFit result:"
        print "T0    = {:7.3f} degC".format (T0)
        print "k     = {:7.3f} degC/A".format (k)
        print "tau   = {:7.3f} s".format (tau)
        print "delta = {:7.3f} s".format (delta)

    # fit analysis (SIMC-PID tunings) for a cascade form PID controller
    Kc   = 1./k * tau/(timeconst + delta)
    tauI = 4 * (timeconst + delta)
    tauD = 0

    # conversion into standard PID parameters
    gainP = Kc * (tauD + tauI)/tauI
    gainI = Kc / tauI
    gainD = Kc * tauD

    return [gainP, gainI, gainD]

def argparseFloat (string):
    """Helper function for arparse float arguments"""
    try:
        value = float(string)
    except ValueError: 
        msg = "{} is not a float value".format(string)
        raise argparse.ArgumentTypeError(msg)

    return value

if __name__ == "__main__":
    """Main program"""

    # argument parsing
    global args
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument ("-o", "--output-file", metavar="FILE", help="write measurement data to FILE", type=argparse.FileType('w'))
    group.add_argument ("-i", "--import-file", metavar="FILE", help="import and analyze measurement data from FILE", type=argparse.FileType('r'))
    parser.add_argument ("-t", "--timeconst", metavar="TIME", help="target PID loop time constant in s (default: 10 s)", type=int, default=10)
    parser.add_argument ("-a", "--address", metavar="ADDR", help="address of power supply (default: {})".format(address), type=int, default=address)
    parser.add_argument ("-s", "--sensor-number", metavar="NUM", help="number of thermocouple sensor (default: {})".format(sensor), type=int, default=sensor)
    parser.add_argument ("-k", "--sensor-type", metavar="TYPE", help="thermocouple sensor type, 'C' or 'K' (default: '{}')".format(tc_type), choices=['C', 'K'], default=tc_type)
    parser.add_argument ("-x", "--stepsize", metavar="STEP", help="current step in A to take (default: {} A)".format(stepsize), type=argparseFloat, default=stepsize)
    parser.add_argument ("-p", "--steptime", metavar="TIME", help="time between start of measurement and current step in s (default: {} s)".format(steptime), type=int, default=steptime)
    parser.add_argument ("-d", "--duration", metavar="TIME", help="duration of data acquisition after temperature step in s (default: {} s)".format(duration), type=int, default=duration)
    parser.add_argument ("-I", "--measure-interval", metavar="TIME", help="time in s between individual temperature measurements (default: {} s)".format(measure_interval), type=int, default=measure_interval)
    parser.add_argument ("-D", "--device", metavar="TTY", help="name of serial device to power supplies (default: {})".format(device), default=device)
    args = parser.parse_args()

    if args.import_file != None:
        # import old data
        xdata, ydata = importdata (args.import_file)
    else:
        # measure new data
        xdata, ydata = measure (verbose = True)

    gainP, gainI, gainD = analysis (xdata, ydata, args.timeconst, verbose = True)
    print "\nRecommended PID settings for {} s response time constant:".format (args.timeconst)
    print "P = {:6.2f} mA/degC".format (1000 * gainP)
    print "I = {:6.2f} mA/(degC*s)".format (1000 * gainI)
    print "D = {:6.2f} mA/(degC/s)".format (1000 * gainD)
