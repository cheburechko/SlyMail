from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'SlyMail.views.home', name='home'),
    # url(r'^SlyMail/', include('SlyMail.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'client.views.login'),
    url(r'^register$', 'client.views.register', name='register'),
    url(r'^client$', 'client.views.client', name='client'),
    url(r'^client/inbox$', 'client.views.inbox', name='inbox'),
    url(r'^client/sent$', 'client.views.sent', name='sent'),
    url(r'^client/trash$', 'client.views.trash', name='trash'),
    url(r'^client/drafts$', 'client.views.drafts', name='drafts'),
    url(r'^client/edit/(?P<pk>\d+)$', 'client.views.edit', name='edit'),
    url(r'^client/read/(?P<pk>\d+)$', 'client.views.read', name='read')
)