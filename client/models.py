from django.db import models


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
    raw_message = models.FileField()


class MessagePart(models.Model):
    message = models.ForeignKey(to=Message)
    content_type = models.CharField(max_length=100)
    file_path = models.FileField()