from django.contrib import admin
from client.models import *

admin.site.register(Message)
admin.site.register(MessagePart)
admin.site.register(AddressBook)
admin.site.register(MailUser)