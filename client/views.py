# Create your views here.
from django.forms import fields
from django import forms
from django.contrib import messages, auth
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.urlresolvers import reverse

from client.models import *

class LoginForm(forms.Form):
    username = fields.CharField(max_length=30, min_length=3)
    password = fields.CharField(max_length=30, widget=forms.PasswordInput)


def login(request):
    redirect_to = request.REQUEST.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].lower()
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                messages.add_message(request, messages.SUCCESS, "Welcome: " + username)
                return HttpResponseRedirect(reverse('client'))
            else:
                messages.add_message(request, messages.ERROR, "Error: no such pair login-password was found")
    else:
        form=LoginForm()
    return render_to_response(template_name='login.html',
                              dictionary={'form': form, 'next': redirect_to},
                              context_instance=RequestContext(request)
    )

def register(request):
    redirect_to = request.REQUEST.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].lower()
            password = form.cleaned_data['password']
            try:
                User.objects.create_user(username=username, password=password)
            except IntegrityError:
                messages.add_message(request, messages.ERROR, "A user with such name already exists")
            else:
                messages.add_message(request, messages.SUCCESS, "Registration completed successfully")
                user = auth.authenticate(username=username, password=password)
                auth.login(request, user)
                return HttpResponseRedirect(reverse('client'))
    else:
        form = LoginForm()
    return render_to_response(template_name='register.html',
                              dictionary={'form': form, 'next': redirect_to},
                              context_instance=RequestContext(request)
    )

def client(request):
    return HttpResponseRedirect(reverse('inbox'))

def show_list(request, type):
    user = get_object_or_404(MailUser, user=request.user)
    result = Message.objects.filter(owner=user, type=type).all()
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


def edit(request, pk):
    raise Http404()


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
    if html_msg.count > 0:
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
    user = get_object_or_404(MailUser, user=request.user)
    msg = get_object_or_404(Message, owner=user, pk=pk)
    msg_part = MessagePart.objects.filter(message=msg)

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