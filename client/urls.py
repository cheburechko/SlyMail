__author__ = 'cheburechko'

from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'SlyMail.views.home', name='home'),
    # url(r'^SlyMail/', include('SlyMail.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^$', 'client.views.client', name='client'),
    url(r'^inbox$', 'client.views.inbox', name='inbox'),
    url(r'^sent$', 'client.views.sent', name='sent'),
    url(r'^trash$', 'client.views.trash', name='trash'),
    url(r'^drafts$', 'client.views.drafts', name='drafts'),
    url(r'^edit/(?P<pk>\d+)$', 'client.views.edit', name='edit'),
    url(r'^read/(?P<pk>\d+)$', 'client.views.read', name='read'),
    url(r'^read/(?P<pk>\d+)/fetch$', 'client.views.fetchMail', name='fetchMail'),
    url(r'^download/(?P<pk>\d+)$', 'client.views.download', name='download'),
    url(r'^process$', 'client.views.process', name="process")
)
