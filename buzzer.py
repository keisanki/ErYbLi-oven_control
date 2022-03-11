#!/usr/bin/python
#-*- coding: latin-1 -*-

import RPi.GPIO as GPIO
import atexit
import time

class Buzzer (object):
    """Object to operate the piezo buzzer.

    This module can either give normal beeps for warning or acknowledgement
    purposes or, as a special treat, do meesages in Morse code.
    """

    # The Morse alphabet
    CODE = {" ": ' ',
            "'": '.----.',
            '(': '-.--.-',
            ')': '-.--.-',
            ',': '--..--',
            '-': '-....-',
            '.': '.-.-.-',
            '/': '-..-.',
            '0': '-----',
            '1': '.----',
            '2': '..---',
            '3': '...--',
            '4': '....-',
            '5': '.....',
            '6': '-....',
            '7': '--...',
            '8': '---..',
            '9': '----.',
            ':': '---...',
            ';': '-.-.-.',
            '?': '..--..',
            'A': '.-',
            'B': '-...',
            'C': '-.-.',
            'D': '-..',
            'E': '.',
            'F': '..-.',
            'G': '--.',
            'H': '....',
            'I': '..',
            'J': '.---',
            'K': '-.-',
            'L': '.-..',
            'M': '--',
            'N': '-.',
            'O': '---',
            'P': '.--.',
            'Q': '--.-',
            'R': '.-.',
            'S': '...',
            'T': '-',
            'U': '..-',
            'V': '...-',
            'W': '.--',
            'X': '-..-',
            'Y': '-.--',
            'Z': '--..',
            '_': '..--.-'}

    DURATION_UNIT = 0.025

    def __init__ (self, buzzer_pin):
        """Create the Buzzer object.

        :param pin: GPIO pin (BCM notation) the buzzer is connected to
        """

        self.buzzer_pin = buzzer_pin

        GPIO.setmode (GPIO.BCM)
        GPIO.setup (self.buzzer_pin, GPIO.OUT)

        atexit.register (self.cleanup)

    def cleanup (self):
        """Free GPIO pin on object destruction"""
        GPIO.cleanup (self.buzzer_pin)

    def _dot (self):
        """Output a dot"""
        GPIO.output (self.buzzer_pin, 1)
        time.sleep (Buzzer.DURATION_UNIT)
        GPIO.output (self.buzzer_pin, 0)
        time.sleep (Buzzer.DURATION_UNIT)
        #print ".",

    def _dash (self):
        """Output a dash"""
        GPIO.output (self.buzzer_pin, 1)
        time.sleep (3 * Buzzer.DURATION_UNIT)
        GPIO.output (self.buzzer_pin, 0)
        time.sleep (Buzzer.DURATION_UNIT)
        #print "_",

    def _gap (self):
        """Wait for the duration between two letters"""
        time.sleep (3 * Buzzer.DURATION_UNIT)
        #print "/",

    def _space (self):
        """Wait for the duration of a space

        Actually the space duration is 7 units. However the gap
        delimiter of 3 units will also be sent, so here we are
        only allowing for 4 additional units waiting time."""
        time.sleep (4 * Buzzer.DURATION_UNIT)
        #print " ",

    def MorseSend (self, msg):
        """Send a message as Morse code to the buzzer

        :param msg: String to be sent (default: none)
        """
        for letter in msg:
            try:
                for symbol in Buzzer.CODE[letter.upper ()]:
                    if symbol == '-':
                        self._dash ()
                    elif symbol == '.':
                        self._dot ()
                    elif symbol == ' ':
                        self._space ()
                    self._gap ()
            except KeyError:
                # ignore unknown symbols
                pass

    def AcknowledgeBeepShort (self, num = 1):
        """Send a very short beep as acknowledgement sound.

        :param num: number of beeps (default: 1)
        """

        while num > 0:
            GPIO.output (self.buzzer_pin, 1)
            time.sleep (0.0005)
            GPIO.output (self.buzzer_pin, 0)
            num -= 1
            if num > 0:
                time.sleep (0.1)

    def AcknowledgeBeepLong (self):
        """Send a longer beep as acknowledgement sound."""

        GPIO.output (self.buzzer_pin, 1)
        time.sleep (0.15)
        GPIO.output (self.buzzer_pin, 0)


if __name__ == '__main__':
    """Just testing"""
    buzzer = Buzzer (4)
    buzzer.MorseSend ("SOS ")
    buzzer.MorseSend ("SOS ")
    buzzer.MorseSend ("SOS ")
    buzzer.MorseSend (" ")
    buzzer.MorseSend (" ")
    buzzer.MorseSend (" ")
    buzzer.AcknowledgeBeepLong ()
    buzzer.MorseSend (" ")
    buzzer.MorseSend (" ")
    buzzer.MorseSend (" ")
    buzzer.MorseSend (" ")
    buzzer.AcknowledgeBeepShort ()
