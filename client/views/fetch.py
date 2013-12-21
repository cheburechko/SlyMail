# Create your views here.
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from client.models import *


def download(request, pk):
    user = get_object_or_404(MailUser, user=request.user)
    msg_part = get_object_or_404(MessagePart, message__owner=user, pk=pk)
    data = msg_part.file_path.read()
    response = HttpResponse(data, content_type=msg_part.content_type)
    response['Content-Disposition'] = 'attachment; filename="' + msg_part.file_name + '"'
    return response


def fetchMail(request, pk):
    user = get_object_or_404(MailUser, user=request.user)
    msg = get_object_or_404(Message, owner=user, pk=pk)
    msg_part = MessagePart.objects.filter(message=msg)

    html_msg = msg_part.filter(content_type='text/html')
    text_list = []

    if html_msg.count() > 0:
        text_list = html_msg.all()
    else:
        text_list = msg_part.filter(content_type='text/plain').all()

    output = ""
    for text in text_list:
        output += text.file_path.read()

    return HttpResponse(output)


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


def read(request, pk):
    msg = get_object_or_404(Message, owner__user=request.user, pk=pk)
    msg_part = msg.messagepart_set

    attachment_parts = msg_part.exclude(content_type='text/html')\
                               .exclude(content_type='text/plain')
    attachments = []
    for attachment in attachment_parts.all():
        attachments.append({"url": reverse('download', args=[attachment.pk]),
                            "name": attachment.file_name,
                            "size": renderSize(os.path.getsize(attachment.file_path.path))})

    return render_to_response(template_name='show_msg.html',
                              dictionary={'fetch': reverse('fetchMail', args=[pk]),
                                          'subject': msg.subject,
                                          'recipients': msg.recipients,
                                          'sender': msg.sender,
                                          'attachments': attachments},
                              context_instance=RequestContext(request)
    )

