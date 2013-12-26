__author__ = 'cheburechko'

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext

from client.models import *

def client(request):
    return HttpResponseRedirect(reverse('inbox'))


def show_list(request, type):
    user = get_object_or_404(MailUser, user=request.user)
    result = Message.objects.filter(owner=user, type=type).order_by('-date').all()
    return render_to_response(template_name='list_mail.html',
                              dictionary={'message_list': result, type: True},
                              context_instance=RequestContext(request))


def inbox(request):
    return show_list(request, 'Inbox')


def sent(request):
    return show_list(request, 'Sent')


def trash(request):
    return show_list(request, 'Trash')


def drafts(request):
    return show_list(request, 'Drafts')