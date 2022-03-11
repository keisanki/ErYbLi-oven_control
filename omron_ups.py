#!/usr/bin/python
#-*- coding: latin-1 -*-
"""Module to obtain status information form an Omron UPS.

The Omron UPS has a SNMP/web card installed and the status is obtained
by retrieving the required information from the status web page.
"""

from lxml import html
import requests

class OmronUPS (object):
    """Obtain UPS status information from the information web page"""

    def __init__ (self, IP):
        """Create and initialize the OmronUPS object.

        :param IP: IP address of the UPS
        """

        self.ip = IP
        self.address = 'PageCompre.html'
        self.xpath = '/html/body/div/table/tr/td[1]/table/tr/td/table/tr[1]/td[1]/table/tr[4]/td[3]/table/td/font/text()'

    def getStatusStr (self):
        """Get the web page data and extract the status string

        :return: UPS status string, "Connection Error" or "Error"
        """

        status = "Error"

        try:
            page = requests.get ('http://' + self.ip + '/' + self.address, timeout = 0.5)
            tree = html.fromstring (page.content)
            status = tree.xpath (self.xpath)
        except requests.exceptions.RequestException as e:
            status = ["Connection Error"]

        if len (status) > 0:
            return status[0]
        else:
            return None

    def getInterlock (self):
        """Get overall UPS interlock status

        :return: List with two elements
                 - 1st element: True on good condition, False on bad condition
                 - 2nd element: status string
        """

        error_conditions = [" ", "Output over voltage", "DC bus voltage error",
                "Output short", "Over load time out", "Battery over charge",
                "Battery under charge", "Over temperature", "External Fan fail",
                "TX fail", "Internal CPU communication error", "Output under voltage",
                "Single Wave Load", "Bat-Config. Fail", "CPU operation failed",
                "Output DC unbalance", "Internal Fan fail","Over Load",
                "Battery Weak", "Battery Empty", "Battery temperature high",
                "UPS life expired", "Inverter current circuit fail",
                "Output current circuit fail", "Voltage reference fail",
                "Output V sensor fail", "DC Voltage sensor fail", "Input frequency fail",
                "Sync. fail", "CPU internal fail", "Input current circuit fail",
                "On Battery", "UPS Power Off", "Error", "Connection Error"]

        status_str = self.getStatusStr ().strip ()
        if status_str in error_conditions:
            return [False, status_str]

        return [True, status_str]


if __name__ == '__main__':
    """Just testing"""
    ups = OmronUPS ('192.168.1.28')
    print ups.getInterlock ()
    print ups.getInterlock ()
