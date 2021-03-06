from django.contrib import admin
from client.models import *


class AddressBookAdmin(admin.ModelAdmin):
    list_display = ['owner', 'name', 'email']

class MessageAdmin(admin.ModelAdmin):
    list_display = ['owner', 'type', 'subject', 'recipients', 'date']

class MessagePartAdmin(admin.ModelAdmin):
    def owner(self, obj):
        return obj.message.owner.user.username

    def subject(self, obj):
        return obj.message.subject

    def type(self, obj):
        return obj.message.type
    list_display = ['owner', 'type', 'subject', 'file_name', 'content_type']


admin.site.register(Message, MessageAdmin)
admin.site.register(MessagePart, MessagePartAdmin)
admin.site.register(AddressBook, AddressBookAdmin)
admin.site.register(MailUser)