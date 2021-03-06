__author__ = 'cheburechko'

from django.contrib import messages
from django.core.files.base import ContentFile
from SlyMail.settings import SMTP_LOCAL_ADDR, EMAIL_REGEX
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse

import smtplib, mimetypes,traceback
from email.utils import getaddresses, formataddr
from email.mime.multipart import MIMEMultipart

from client.models import *
from client.views.helpers import *


def edit(request, pk):
    owner = get_object_or_404(MailUser, user=request.user)
    msg = get_object_or_404(Message, pk=pk, owner=owner)
    try:
        msg_part = msg.messagepart_set.get(is_attachment=False)
    except:
        traceback.print_exc()
        raise Http404

    form = EditMailForm({'to': msg.recipients,
                         'subject': msg.subject,
                         'body': msg_part.file_path.read()})
    msg_part.file_path.close()

    addresses = []
    for address in AddressBook.objects.filter(owner=owner):
        addresses.append(formataddr((address.name, address.email)))

    return render_to_response(template_name='edit_message.html',
                              dictionary={'form': form,
                                          'msg_pk': msg.pk,
                                          'msg_part_pk': msg_part.pk,
                                          'attachments': collect_attachments(msg),
                                          'addresses': addresses},
                              context_instance=RequestContext(request)
    )


def deleteAttachment(request):
    owner = get_object_or_404(MailUser, user=request.user)
    if 'pk' in request.POST:
        pk = int(request.POST['pk'])
        part = get_object_or_404(MessagePart, message__owner=owner,
                                 pk=pk)
        part.delete()

    return HttpResponse()


def save_mail(request, pk):
    result = save_msg(request, pk)

    if result is None:
        messages.add_message(request, messages.SUCCESS, "Email was saved successfully.")
    else:
        messages.add_message(request, messages.ERROR, result)
    return HttpResponseRedirect(reverse('edit', args=[pk]))


def send_mail(request, pk):
    errors = save_msg(request, pk)
    msg = get_object_or_404(Message,
                            pk=pk,
                            owner__user=request.user)

    # Check email addresses consistency.
    recipients = []
    for (name, addr) in getaddresses([msg.recipients]):
        if not EMAIL_REGEX.match(addr) and addr != "":
            messages.add_message(request, messages.ERROR,
                                 '"'+addr+'" is not a valid email address.')
            return HttpResponseRedirect(reverse('edit', args=[msg.pk]))
        recipients += [addr]

    # Construct mail message.
    mail = MIMEMultipart()
    for msg_part in msg.messagepart_set.all():
        mail.attach(convert_msg_part(msg_part))
    mail['From'] = formataddr((msg.owner.name, msg.owner.address))
    mail['To'] = msg.recipients
    mail['Subject'] = msg.subject
    msg.raw_message.save(msg.pk.__str__(), ContentFile(mail.as_string()))

    # Send it to our SMTP server.
    server = smtplib.SMTP(SMTP_LOCAL_ADDR[0], SMTP_LOCAL_ADDR[1])
    try:
        server.ehlo()
        server.sendmail(msg.sender, recipients, mail.as_string())
        msg.type = 'Sent'
        msg.save()
    except:
        traceback.print_exc()
    finally:
        server.quit()

    return HttpResponseRedirect(reverse('inbox'))


def upload(request, pk):
    msg = get_object_or_404(Message,
                            owner__user=request.user,
                            pk=pk)

    try:
        msg_part = MessagePart()
        uploaded_file = request.FILES['file']

        msg_part.file_name = uploaded_file.name
        msg_part.is_attachment = True
        msg_part.message = msg
        msg_part.file_size = uploaded_file.size

        msg_part.content_type, encoding = \
            mimetypes.guess_type(msg_part.file_name)
        if msg_part.content_type is None or encoding is not None:
            msg_part.content_type = 'application/octet-stream'

        msg_part.file_path.save(msg_part.file_name, uploaded_file)
        msg_part.save()

        return HttpResponse(u'<div class="row" id="attachment_{0}">'
                            u'<a href="{1}">{2}</a> - {3}'
                            u'<button class="btn btn-default" type="button" onclick="deleteFile({0})">'
                            u'<span class="glyphicon glyphicon-remove"></span>'
                            u'</button>'
                            u'</div>'\
            .format(msg_part.pk,
                    reverse('download', args=[msg_part.pk]),
                    msg_part.file_name,
                    renderSize(msg_part.file_size)))
    except:
        traceback.print_exc()
        return HttpResponse('<p class="alert alert-danger">Failed to upload file.</p>')


def delete_mail(request, pk):
    delete_msg(request, pk)
    return HttpResponseRedirect(reverse('client'))


def resend_mail(request, pk):
    msg = get_object_or_404(Message, owner__user=request.user, pk=pk)

    copy = Message()
    copy.owner = msg.owner
    copy.sender = msg.sender
    copy.date = datetime.datetime.now()
    copy.recipients = msg.recipients
    copy.subject = msg.subject
    copy.type = 'Drafts'
    copy.raw_message.save(msg.raw_message.name,
                          ContentFile(msg.raw_message.read()))
    msg.raw_message.close()
    copy.save()

    for part in msg.messagepart_set.all():
        copy_part = MessagePart()
        copy_part.content_type = part.content_type
        copy_part.file_name = part.file_name
        copy_part.file_size = part.file_size
        copy_part.message = copy
        copy_part.is_attachment = part.is_attachment
        copy_part.save()

        copy_part.file_path.save(part.file_name,
                                 ContentFile(part.file_path.read()))
        part.file_path.close()
        copy_part.save()

    return edit(request, copy.pk)


def reply(request, pk):
    owner = get_object_or_404(MailUser, user=request.user)
    msg = get_object_or_404(Message, pk=pk, owner=owner)
    msg_part = msg.messagepart_set.get(is_attachment=False)

    reply_msg = Message.objects.get(pk=new_msg(request))
    reply_msg.subject = 'Re: ' + msg.subject
    reply_msg.recipients = msg.sender

    reply_part = reply_msg.messagepart_set.all()[0]
    reply_part.file_path.save(reply_part.file_name, ContentFile(
        unicode(msg.date) + u' ' + unicode(msg.sender) + u'\n'
        u'========================================================\n' +
        msg_part.file_path.read() +
        u'========================================================\n\n' +
        owner.signature
    ))
    msg_part.file_path.close()
    reply_msg.save()
    reply_part.save()

    return edit(request, reply_msg.pk)


# Busy box for all buttons.
def processSingle(request, pk):
    if 'resend' in request.POST:
        return resend_mail(request, pk)
    elif 'save' in request.POST:
        return save_mail(request, pk)
    elif 'send' in request.POST:
        return send_mail(request, pk)
    elif 'upload' in request.POST:
        return upload(request, pk)
    elif 'delete' in request.POST:
        return delete_mail(request, pk)
    elif 'new' in request.POST:
        return edit(request, new_msg(request))
    elif 'reply' in request.POST:
        return reply(request, pk)
    else:
        raise Http404