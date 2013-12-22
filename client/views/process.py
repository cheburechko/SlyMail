__author__ = 'cheburechko'

from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from SlyMail.settings import SERVER_DOMAIN
from django.core.files.base import ContentFile

import datetime

from client.models import *
from client.views.processSingle import edit


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
                    if part.file_path != '':
                        part.file_path.delete()
                if msg.raw_message != '':
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


def process(request):
    if 'new' in request.POST:
        return new_mail(request)
    if 'delete' in request.POST:
        return delete(request)
    else:
        raise Http404