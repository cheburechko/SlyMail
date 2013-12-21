__author__ = 'cheburechko'

from django.forms import fields
from django import forms
from django.contrib import messages
from django.core.files.base import ContentFile
from SlyMail.settings import SERVER_DOMAIN, SMTP_LOCAL_ADDR
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

import datetime, re, smtplib, mimetypes
from email.utils import getaddresses
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.encoders import encode_base64

from client.models import *
from client.views.helpers import collect_attachements, renderSize

class EditMailForm(forms.Form):
    to = fields.CharField(required=False)
    subject = fields.CharField(required=False)
    body = fields.CharField(widget=forms.Textarea, required=False)
    #file = fields.FileField


def edit(request, pk):
    msg = Message.objects.get(pk=pk, owner__user=request.user)
    try:
        msg_part = msg.messagepart_set.get(content_type='text/plain')
    except:
        raise Http404

    form = EditMailForm({'to': msg.recipients,
                         'subject': msg.subject,
                         'body': msg_part.file_path.read()})
    return render_to_response(template_name='edit_message.html',
                              dictionary={'form': form,
                                          'msg_pk': msg.pk,
                                          'msg_part_pk': msg_part.pk,
                                          'attachments': collect_attachements(msg)},
                              context_instance=RequestContext(request)
    )


def delete(request):
    for key in request.POST.keys():
        if key.startswith('check'):
            pk = int(key[5:])
            msg = get_object_or_404(Message, pk=pk, owner__user=request.user)
            if msg.type != 'Trash':
                msg.type = 'Trash'
                msg.save()
                messages.add_message(request, messages.SUCCESS, "Mail was moved to Trash")
            else:
                for part in msg.messagepart_set.all():
                    part.file_path.delete()
                msg.raw_message.delete()
                msg.delete()
                messages.add_message(request, messages.SUCCESS, "Mail was deleted")

    return HttpResponseRedirect(reverse('client'))


def new_mail(request):
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

    return edit(request, msg.pk)


def save_mail(request):
    msg = get_object_or_404(Message,
                            pk=request.POST['msg_pk'],
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
        messages.add_message(request, messages.SUCCESS, "Email was saved successfully.")
    else:
        messages.add_message(request, messages.ERROR, form.errors)
    return HttpResponseRedirect(reverse('edit', args=[msg.pk]))


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

EMAIL_REGEX = re.compile(r'^[a-zA-z0-9._\-+%]+@[a-zA-z0-9\-.]+.[a-z]+')


def send_mail(request):
    msg = get_object_or_404(Message,
                            pk=request.POST['msg_pk'],
                            owner__user=request.user)

    # Check email addresses consistency.
    recipients = []
    for (name, addr) in getaddresses([msg.recipients]):
        if not EMAIL_REGEX.match(addr):
            messages.add_message(request, messages.ERROR,
                                 '"'+addr+'" is not a valid email address.')
            return HttpResponseRedirect(reverse('edit', args=[msg.pk]))
        recipients += [addr]

    # Construct mail message.
    mail = MIMEMultipart()
    for msg_part in msg.messagepart_set.all():
        mail.attach(convert_msg_part(msg_part))
    mail['From'] = msg.sender
    mail['To'] = msg.recipients
    mail['Subject'] = msg.subject
    msg.raw_message.save(msg.pk.__str__(), ContentFile(mail.as_string()))

    # Send it to our SMTP server.
    try:
        server = smtplib.SMTP(SMTP_LOCAL_ADDR[0], SMTP_LOCAL_ADDR[1])
        server.ehlo()
        server.sendmail(msg.sender, recipients, mail.as_string())

        msg.type = 'Sent'
        msg.save()
    finally:
        server.quit()

    return HttpResponseRedirect(reverse('inbox'))


def upload(request):
    msg = get_object_or_404(Message,
                            owner__user=request.user,
                            pk=request.POST['msg_pk'])

    try:
        msg_part = MessagePart()
        uploaded_file = request.FILES['file']

        msg_part.file_name = uploaded_file.name
        msg_part.message = msg
        msg_part.file_size = uploaded_file.size
        msg_part.file_path.save(msg_part.file_name, uploaded_file)
        msg_part.save()

        return HttpResponse('<div class="form-row">\
        <a href="{:s}">{:s}</a> - {:s}\
        </div>'.format(reverse('download', args=[msg_part.pk]),
                       msg_part.file_name,
                       renderSize(msg_part.file_size)))
    except:
        return HttpResponse('<p class="alert alert-danger">Failed to upload file.</p>')


# Busy box for all buttons.
def process(request):
    if 'delete' in request.POST:
        return delete(request)
    elif 'new' in request.POST:
        return new_mail(request)
    elif 'resend' in request.POST:
        return HttpResponseRedirect(reverse('client'))
    elif 'save' in request.POST:
        return save_mail(request)
    elif 'send' in request.POST:
        return send_mail(request)
    elif 'upload' in request.POST:
        return upload(request)
    else:
        raise Http404