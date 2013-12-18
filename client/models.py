from django.db import models
import os
from SlyMail.settings import MESSAGE_PART_ROOT, MESSAGE_ROOT

class User(models.Model):
    nickname = models.CharField(max_length=30, primary_key=True);
    password = models.CharField(max_length=128)


class AddressBook(models.Model):
    owner = models.ForeignKey(to=User)
    email = models.EmailField()


class Message(models.Model):
    sender = models.EmailField()
    owner = models.ForeignKey(to=User)
    date = models.DateTimeField()
    subject = models.TextField()
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
    content_type = models.CharField(max_length=100)
    file_path = models.FileField(upload_to=get_upload_path)
    pass;