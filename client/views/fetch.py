# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from client.models import *
from client.views.helpers import renderSize, collect_attachments


def download(request, pk):
    user = get_object_or_404(MailUser, user=request.user)
    msg_part = get_object_or_404(MessagePart, message__owner=user, pk=pk)
    data = msg_part.file_path.read()
    msg_part.file_path.close()
    response = HttpResponse(data, content_type=msg_part.content_type)
    response['Content-Disposition'] = 'attachment; filename="' + msg_part.file_name.encode('utf-8') + '"'
    return response


def fetchMail(request, pk):
    msg = get_object_or_404(Message, owner__user=request.user, pk=pk)
    parts = msg.messagepart_set.filter(is_attachment=False)
    html = parts.filter(content_type='text/html')

    if html.count() > 0:
        text_list = html.all()
    else:
        text_list = parts.filter(content_type='text/plain')

    output = ""
    for text in text_list:
        output += text.file_path.read()
        text.file_path.close()

    return HttpResponse(output)


def read(request, pk):
    owner = MailUser.objects.get(user=request.user)
    msg = get_object_or_404(Message, owner=owner, pk=pk)
    print msg.sender == owner.address
    return render_to_response(template_name='show_msg.html',
                              dictionary={'fetch': reverse('fetchMail', args=[pk]),
                                          'subject': msg.subject,
                                          'recipients': msg.recipients,
                                          'sender': msg.sender,
                                          'msg_pk': pk,
                                          'can_resend': msg.sender == owner.address,
                                          'attachments': collect_attachments(msg)},
                              context_instance=RequestContext(request)
    )

