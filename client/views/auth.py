__author__ = 'cheburechko'

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib import messages, auth
from django.forms import fields
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from client.models import MailUser

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


def logout(request):
    redirect_to = reverse('login')
    auth.logout(request)
    messages.add_message(request, messages.SUCCESS, "Logged out successfully")
    return HttpResponseRedirect(redirect_to)


def register(request):
    redirect_to = request.REQUEST.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].lower()
            password = form.cleaned_data['password']
            try:
                user = User.objects.create_user(username=username, password=password)
                MailUser.objects.create(user=user)
            except IntegrityError:
                messages.add_message(request, messages.ERROR, "A user with such name already exists")
            else:
                messages.add_message(request, messages.SUCCESS, "Registration completed successfully")
                user = auth.authenticate(username=username, password=password)
                auth.login(request, user)
                return HttpResponseRedirect(reverse('login'))
    else:
        form = LoginForm()
    return render_to_response(template_name='register.html',
                              dictionary={'form': form, 'next': redirect_to},
                              context_instance=RequestContext(request)
    )