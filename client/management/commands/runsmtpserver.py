from django.core.management.base import NoArgsCommand
from SlyMail.settings import *
from client.views.helpers import header_to_unicode
from client.models import *
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from email.parser import Parser
from email.utils import getaddresses, parseaddr
from django.core.files.base import ContentFile
import traceback

import smtpd, smtplib
import asyncore


class MailSMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data):
        if DEBUG:
            print 'Receiving message from:', peer
            print 'Message addressed from:', mailfrom
            print 'Message addressed to  :', rcpttos
            print 'Message length        :', len(data)

        for recipient in rcpttos:
            list = recipient.split('@')
            if len(list) > 1:
                if list[1] != SERVER_DOMAIN:
                    # Forward outgoing messages.
                    #   if peer[0] == SMTP_LOCAL_ADDR[0]:
                    #       try:
                    #          server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
                    #          server.set_debuglevel(True)
                    #          server.ehlo()
                    #          if EMAIL_USE_TLS:
                    #               server.starttls()
                    #               server.ehlo()
                    #
                    #          server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
                    #          server.sendmail(mailfrom, rcpttos, data)
                    #       finally:
                    #          server.quit()
                    continue

            try:
                user = MailUser.objects.get(user__username=list[0])
                parser = Parser()
                mail = parser.parsestr(data)

                message = Message()
                message.sender =  header_to_unicode(mail['From'])
                message.owner = user
                message.date = datetime.now()
                message.subject = header_to_unicode(mail['Subject'])
                message.type = "Inbox"
                message.recipients = header_to_unicode(mail['To'])

                all_recipients = getaddresses([message.recipients])

                for realname, address in all_recipients:
                    AddressBook.objects .get_or_create(owner=user, email=address,
                                              defaults={'name': realname})

                realname, address = parseaddr(message.sender)
                AddressBook.objects.get_or_create(owner=user, email=address,
                                          defaults={'name': realname})

                # Save raw content just in case
                message.save()
                message.raw_message.save(message.pk.__str__(), ContentFile(data))
                message.save()
                print 'Saved raw message:', message.pk

                # Decode attachments and text message.
                for part in mail.walk():
                    if part.is_multipart():
                        continue

                    msg_part = MessagePart()
                    msg_part.message = message
                    msg_part.content_type = part.get_content_type()
                    part_data = part.get_payload(decode=True)
                    msg_part.file_size = len(part_data)

                    if part['Content-Disposition'] is not None:
                        msg_part.is_attachment = True;

                    msg_part.save()

                    part_name = part.get_filename(msg_part.pk.__str__())
                    msg_part.file_path.save(part_name,
                                            ContentFile(part_data))
                    msg_part.file_name = part_name;
                    msg_part.save()
                    print 'Saved part ', part_name
                print 'Successfully received'
            except ObjectDoesNotExist:
                print list[0], ' not in db'
            except:
                traceback.print_exc()


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        server = MailSMTPServer(SMTP_LOCAL_ADDR, None)
        asyncore.loop()
