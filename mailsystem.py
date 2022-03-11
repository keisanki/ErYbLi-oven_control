#!/usr/bin/python
#-*- coding: latin-1 -*-
"""Module for sending all sorts of messages via e-mail to a list of recipients"""

from mailer import Mailer
from mailer import Message

class MailSystem (object):
    """MailSystem handles sending of normal status messages as well as warning 
    messages to a list of users"""

    SENDER = "oven@somedomain.jp"

    def __init__ (self, recipients = [], smtp_server = "192.168.1.11"):
        """Create the object.
        
        :param recipients: list of mail addresses (default: empty list)
        """

        self.sender = Mailer (smtp_server)
        self.recipients = recipients

    def sendMessage (self, subject, body):
        """Send a message.
        It will be sent to the list of recipients specified earlier.

        :param subject: Message subject
        :param body: Message body text
        """

        if (len (self.recipients) == 0):
            return

        message = Message (From = MailSystem.SENDER, To = self.recipients, charset = "utf-8")
        message.Subject = subject
        message.Body = body
        self.sender.send (message)


if __name__ == '__main__':
    ms = MailSystem (["test@testdomain.jp"])
    ms.sendMessage ("Test", "Just a test message.\n\nFlorian")
