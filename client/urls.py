__author__ = 'cheburechko'

from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'SlyMail.views.home', name='home'),
    # url(r'^SlyMail/', include('SlyMail.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^$', 'client.views.list.client', name='client'),
    url(r'^inbox$', 'client.views.list.inbox', name='inbox'),
    url(r'^sent$', 'client.views.list.sent', name='sent'),
    url(r'^trash$', 'client.views.list.trash', name='trash'),
    url(r'^drafts$', 'client.views.list.drafts', name='drafts'),
    url(r'^edit/(?P<pk>\d+)$', 'client.views.processSingle.edit', name='edit'),
    url(r'^read/(?P<pk>\d+)$', 'client.views.fetch.read', name='read'),
    url(r'^read/(?P<pk>\d+)/fetch$', 'client.views.fetch.fetchMail', name='fetchMail'),
    url(r'^download/(?P<pk>\d+)$', 'client.views.fetch.download', name='download'),
    url(r'^process$', 'client.views.process.process', name="process"),
    url(r'^process/(?P<pk>\d+)$', 'client.views.processSingle.processSingle', name="processSingle")
)
