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
from SlyMail.settings import SERVER_DOMAIN
from client.views.helpers import BootstrapForm

class LoginForm(BootstrapForm):
    username = fields.CharField(
        max_length=30,
        min_length=3,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = fields.CharField(
        max_length=30,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class RegistrationForm(LoginForm):
    real_name = fields.CharField(
        max_length=80, required=False, initial='Anonymous',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('client'))
    else:
        return HttpResponseRedirect(reverse('login'))


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
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].lower()
            password = form.cleaned_data['password']
            try:
                user = User.objects.create_user(username=username, password=password)
                MailUser.objects.create(user=user,
                                        name=form.cleaned_data['real_name'],
                                        address=username+'@'+SERVER_DOMAIN)
            except IntegrityError:
                messages.add_message(request, messages.ERROR, "A user with such name already exists")
            else:
                messages.add_message(request, messages.SUCCESS, "Registration completed successfully")
                user = auth.authenticate(username=username, password=password)
                auth.login(request, user)
                return HttpResponseRedirect(reverse('login'))
    else:
        form = RegistrationForm()
    return render_to_response(template_name='register.html',
                              dictionary={'form': form, 'next': redirect_to},
                              context_instance=RequestContext(request)
    )