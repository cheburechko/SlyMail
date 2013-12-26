__author__ = 'cheburechko'

from django.core.urlresolvers import reverse
from django.forms import fields
from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile

import os, datetime, traceback
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.encoders import encode_base64
from email.header import decode_header

from client.models import *


class BootstrapForm(forms.Form):
    def render(self):
        return self._html_output(
            normal_row = u'<div class="input-group">' \
                         u'<span class="input-group-addon">%(label)s</span>' \
                         u'%(field)s%(help_text)s %(errors)s</div>',
            error_row = u'<div class="error">%s</div>',
            row_ender = u'</div>',
            help_text_html = u'<div class="help-text">%s</div>',
            errors_on_separate_row = False
        )

class EditMailForm(BootstrapForm):
    to = fields.CharField(required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    subject = fields.CharField(required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    body = fields.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows':15}),
                            required=False, label='')




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
    attachment_parts = msg.messagepart_set.exclude(is_attachment=False)
    attachments = []
    for attachment in attachment_parts.all():
        attachments.append({"url": reverse('download', args=[attachment.pk]),
                            "name": attachment.file_name,
                            "size": renderSize(os.path.getsize(attachment.file_path.path)),
                            "pk": attachment.pk})
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
        msg.date = datetime.datetime.now()
        if msg_part.file_path:
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

    if msg_part.is_attachment:
        msg.add_header('Content-Disposition', 'attachment',
                       filename=('utf-8', 'ru', msg_part.file_name.encode('utf-8')))
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
    msg.owner = MailUser.objects.get(user=request.user)
    msg.sender = msg.owner.address
    msg.date = datetime.datetime.now()
    msg.save()

    msg_part = MessagePart()
    msg_part.content_type = 'text/plain'
    msg_part.file_size = 0
    msg_part.message = msg
    msg_part.save()

    msg_part.file_name = msg_part.pk.__str__()
    msg_part.file_path.save(msg_part.file_name,
                            ContentFile(u'\n\n' + msg.owner.signature))
    return msg.pk


def header_to_unicode(header):
    default_charset = 'ASCII'
    buffer = decode_header(header)
    return u' '.join(unicode(head[0], head[1] or default_charset)
                          for head in buffer)