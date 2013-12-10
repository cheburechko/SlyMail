from django.core.management.base import NoArgsCommand
from SlyMail.settings import *

import smtpd
import asyncore

class MailSMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data):
        print 'Receiving message from:', peer
        print 'Message addressed from:', mailfrom
        print 'Message addressed to  :', rcpttos
        print 'Message length        :', len(data)
        return

class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        server = MailSMTPServer(SMTP_LOCAL_ADDR, None)
        asyncore.loop()
