__author__ = 'cheburechko'
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.forms import *
from django.contrib import messages

from client.models import *
from client.views.helpers import renderSize, BootstrapForm


class SettingsForm(BootstrapForm):
    mailbox = EmailField(widget=TextInput(attrs={'class': 'form-control'}))
    name = CharField(widget=TextInput(attrs={'class': 'form-control'}),
                     max_length=MailUser._meta.get_field('name').max_length)
    signature = CharField(required=False, widget=Textarea(attrs={'class': 'form-control'}))


def settings(request):
    owner = get_object_or_404(MailUser, user=request.user)

    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            owner.name = form.cleaned_data['name']
            owner.signature = form.cleaned_data['signature']
            owner.address = form.cleaned_data['mailbox']
            owner.save()
            messages.add_message(request, messages.SUCCESS, 'Mail was successfully saved.')
        else:
            messages.add_message(request, messages.ERROR, form.errors)
    else:
        form = SettingsForm({'name': owner.name,
                             'mailbox': owner.address,
                             'signature': owner.signature})

    return render_to_response(template_name='settings.html',
                              dictionary={'form': form},
                              context_instance=RequestContext(request))


def files(request):
    msg_parts = MessagePart.objects.filter(
        message__owner__user=request.user,
        is_attachment=True
    )
    attachments = []
    for part in msg_parts:
        attachments.append({
            'link': reverse('download', args=[part.pk]),
            'name': part.file_name,
            'size': renderSize(part.file_size),
        })
    return render_to_response(template_name='file_list.html',
                              dictionary={'files': attachments},
                              context_instance=RequestContext(request))



def address_book(request):
    owner = get_object_or_404(MailUser, user=request.user)
    addresses = AddressBook.objects.filter(owner=owner)
    if request.method == 'POST':
        for address in addresses.all():
            if 'address_' + str(address.pk) in request.POST:
                address.delete()
            elif 'address_name_' + str(address.pk) in request.POST:
                address.name = request.POST['address_name_' + str(address.pk)]
                address.save()
            email_const = 'new_address_email_'
        for key, value in request.POST.items():
            if key.startswith(email_const):
                pk = int(key[len(email_const):])
                email = value;
                name = request.POST['new_address_name_' + str(pk)]
                AddressBook.objects.create(owner=owner, email=email, name=name)

    result = AddressBook.objects.filter(owner__user=request.user).all()
    return render_to_response(
        template_name='address_book.html',
        dictionary={'addresses':result,
            'name_length':AddressBook._meta.get_field('name').max_length
        },
        context_instance=RequestContext(request)
    )