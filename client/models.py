from django.db import models
from django.contrib.auth.models import User
import os
from SlyMail.settings import MESSAGE_PART_ROOT, MESSAGE_ROOT


class MailUser(models.Model):
    user = models.OneToOneField(User)
    address = models.EmailField(unique=True)
    name = models.CharField(max_length=80, blank=True)
    signature = models.TextField(blank=True)
    # other data comes along


class AddressBook(models.Model):
    owner = models.ForeignKey(to=User)
    email = models.EmailField()
    name = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('owner', 'email',)


class Message(models.Model):
    sender = models.EmailField()
    owner = models.ForeignKey(to=MailUser)
    date = models.DateTimeField()
    subject = models.TextField(blank=True)
    recipients = models.CharField(max_length=1000)
    type_choices = (
        ("Inbox", "Inbox"),
        ("Sent", "Sent"),
        ("Trash", "Trash"),
        ("Drafts", "Drafts")
    )
    type = models.CharField(choices=type_choices, max_length=10)
    raw_message = models.FileField(upload_to=MESSAGE_ROOT)


def get_upload_path(instance, filename):
    return os.path.join(MESSAGE_PART_ROOT, instance.message.pk.__str__(), filename)


class MessagePart(models.Model):
    message = models.ForeignKey(to=Message)
    content_type = models.CharField(max_length=100, blank=False)
    file_path = models.FileField(upload_to=get_upload_path)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()