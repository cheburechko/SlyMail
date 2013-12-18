from django.core.management.base import NoArgsCommand
from SlyMail.settings import *
from client.models import Message, MessagePart, User
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from email.parser import Parser
from django.core.files.base import ContentFile
import traceback

import smtpd
import asyncore

class MailSMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data):
        if DEBUG:
            print 'Receiving message from:', peer
            print 'Message addressed from:', mailfrom
            print 'Message addressed to  :', rcpttos
            print 'Message length        :', len(data)
            print 'Message:\n', data

        for recipient in rcpttos:
            list = recipient.split('@')
            if list[1] != SERVER_DOMAIN:
                continue

            try:
                user = User.objects.get(nickname=list[0])
                message = Message()
                message.sender = mailfrom
                message.owner = user
                message.date = datetime.now()

                parser = Parser()
                mail = parser.parsestr(data)
                message.subject = mail['subject']
                message.type = "Inbox"

                # Save raw content just in case
                message.save()
                message.raw_message.save(message.pk.__str__(), ContentFile(data))
                message.save()

                # Decode attachments and text message.
                for part in mail.walk():
                    if part.is_multipart():
                        continue

                    msg_part = MessagePart()
                    msg_part.message = message
                    msg_part.content_type = part.get_content_type()
                    msg_part.save()

                    part_data = part.get_payload(decode=True)
                    part_name = part.get_filename(msg_part.pk.__str__())
                    msg_part.file_path.save(part_name,
                                            ContentFile(part_data))
                    msg_part.save()

            except ObjectDoesNotExist:
                print list[0], ' not in db'
            except:
                traceback.print_exc()


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        server = MailSMTPServer(SMTP_LOCAL_ADDR, None)
        asyncore.loop()
