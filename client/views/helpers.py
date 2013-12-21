__author__ = 'cheburechko'

from django.core.urlresolvers import reverse
import os

def renderSize(size):
    level = 0
    while size >= 1024:
        size /= 1024.0
        level += 1
    unit = ""
    if level == 0:
        unit = "B"
    elif level == 1:
        unit = "KB"
    elif level == 2:
        unit = "MB"
    elif level == 3:
        unit = "GB"
    else:
        raise Exception
    return '{:.1f}{:s}'.format(size, unit)

def collect_attachements(msg):
    attachment_parts = msg.messagepart_set.exclude(content_type='text/html')\
                                          .exclude(content_type='text/plain')
    attachments = []
    for attachment in attachment_parts.all():
        attachments.append({"url": reverse('download', args=[attachment.pk]),
                            "name": attachment.file_name,
                            "size": renderSize(os.path.getsize(attachment.file_path.path))})
    return attachments
