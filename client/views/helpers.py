__author__ = 'cheburechko'

from django.core.urlresolvers import reverse
from django.forms import fields
from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile

import os, datetime
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.encoders import encode_base64

from client.models import *
from SlyMail.settings import SERVER_DOMAIN


class EditMailForm(forms.Form):
    to = fields.CharField(required=False)
    subject = fields.CharField(required=False)
    body = fields.CharField(widget=forms.Textarea, required=False)


def renderSize(size):
    level = 0
    while size >= 1024:
        size /= 1024.0
        level += 1
    unit = ""
    if level == 0:
        unit = "B"
    elif level == 1:
        unit = "KB"
    elif level == 2:
        unit = "MB"
    elif level == 3:
        unit = "GB"
    else:
        raise Exception
    return '{:.1f}{:s}'.format(size, unit)


def collect_attachments(msg):
    attachment_parts = msg.messagepart_set.exclude(content_type='text/html')\
                                          .exclude(content_type='text/plain')
    attachments = []
    for attachment in attachment_parts.all():
        attachments.append({"url": reverse('download', args=[attachment.pk]),
                            "name": attachment.file_name,
                            "size": renderSize(os.path.getsize(attachment.file_path.path))})
    return attachments


def save_msg(request, pk):
    msg = get_object_or_404(Message,
                            pk=pk,
                            owner__user=request.user)
    msg_part = get_object_or_404(MessagePart,
                                 pk=request.POST['msg_part_pk'],
                                 message=msg)

    form = EditMailForm(request.POST)

    if form.is_valid():
        msg.subject = form.cleaned_data['subject']
        msg.recipients = form.cleaned_data['to']
        msg_part.file_path.delete()
        msg_part.file_path.save(msg_part.file_name,
                                ContentFile(form.cleaned_data['body']))
        msg.save()
        msg_part.save()
        return None
    else:
        return form.errors


def convert_msg_part(msg_part):
    msg = None
    data = msg_part.file_path.read()
    msg_part.file_path.close()
    maintype, subtype = msg_part.content_type.split('/', 1)

    if maintype == 'text':
        # Warning! Encoding problems are awaited.
        msg = MIMEText(data, _subtype=subtype)
    elif maintype == 'image':
        msg = MIMEImage(data, _subtype=subtype)
    elif maintype == 'audio':
        msg = MIMEAudio(data, _subtype=subtype)
    else:
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(data)
        encode_base64(msg)

    msg.add_header('Content-Disposition', 'attachment', filename=msg_part.file_name)
    return msg


def delete_msg(request, pk):
    msg = get_object_or_404(Message, pk=pk, owner__user=request.user)
    if msg.type != 'Trash':
        msg.type = 'Trash'
        msg.save()
        messages.add_message(request, messages.SUCCESS, "Mail was moved to Trash")
    else:
        for part in msg.messagepart_set.all():
            if part.file_path != '':
                part.file_path.delete()
        if msg.raw_message != '':
            msg.raw_message.delete()
        msg.delete()
        messages.add_message(request, messages.SUCCESS, "Mail was deleted")


def new_msg(request):
    msg = Message()
    msg.type = 'Drafts'
    msg.sender = request.user.username + '@' + SERVER_DOMAIN
    msg.owner = MailUser.objects.get(user=request.user)
    msg.date = datetime.datetime.now()
    msg.save()

    msg_part = MessagePart()
    msg_part.content_type = 'text/plain'
    msg_part.file_size = 0
    msg_part.message = msg
    msg_part.save()

    msg_part.file_name = msg_part.pk.__str__()
    msg_part.file_path.save(msg_part.file_name,
                            ContentFile(''))
    return msg.pk
