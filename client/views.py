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
from django.core.files.base import ContentFile

import datetime

from client.models import *
from SlyMail.settings import SERVER_DOMAIN


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
                                          'msg_part_pk': msg_part.pk},
                              context_instance=RequestContext(request)
    )


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
        raise Http404
    else:
        raise Http404