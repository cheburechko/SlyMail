# Create your views here.
from django.forms import fields
from django import forms
from django.contrib import messages, auth
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.urlresolvers import reverse

from client.models import Message, MailUser

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

def read(request, pk):

    raise Http404()