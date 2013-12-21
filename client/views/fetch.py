# Create your views here.
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from client.models import *
from client.views.helpers import renderSize, collect_attachements

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


def read(request, pk):
    msg = get_object_or_404(Message, owner__user=request.user, pk=pk)

    return render_to_response(template_name='show_msg.html',
                              dictionary={'fetch': reverse('fetchMail', args=[pk]),
                                          'subject': msg.subject,
                                          'recipients': msg.recipients,
                                          'sender': msg.sender,
                                          'attachments': collect_attachements(msg)},
                              context_instance=RequestContext(request)
    )

