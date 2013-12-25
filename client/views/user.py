__author__ = 'cheburechko'
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from client.models import *

def settings(request):
    raise Http404


def files(request):
    raise Http404


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