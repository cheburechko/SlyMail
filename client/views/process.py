__author__ = 'cheburechko'

from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from client.views.processSingle import edit
from client.views.helpers import delete_msg, new_msg


def delete(request):
    for key in request.POST.keys():
        print 'deleting ', key
        if key.startswith('check'):
            pk = int(key[5:])
            delete_msg(request, pk)

    return HttpResponseRedirect(reverse('client'))


def new_mail(request):
    return edit(request, new_msg(request))


def process(request):
    if 'new' in request.POST:
        return new_mail(request)
    elif 'delete' in request.POST:
        return delete(request)
    else:
        raise Http404