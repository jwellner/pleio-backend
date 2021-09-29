from core.models.comment import CommentMixin
import json
import re
import signal_disabler
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from django.db import connection
from core.models import CommentAttachment, EntityAttachment, GroupAttachment


class Command(BaseCommand):
    help = 'Add size of attachments uploaded in content'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @signal_disabler.disable()
    def handle(self, *args, **options):

        if connection.schema_name == 'public':
            return

        updated_attachments = 0
        attachment_errors = 0

        for attachment in CommentAttachment.objects.all():
            try:
                attachment.size = attachment.upload.size
                attachment.save()
                updated_attachments+=1
            except Exception:
                attachment_errors+=1
                pass

        for attachment in EntityAttachment.objects.all():
            try:
                attachment.size = attachment.upload.size
                attachment.save()
                updated_attachments+=1
            except Exception:
                attachment_errors+=1
                pass

        for attachment in GroupAttachment.objects.all():
            try:
                attachment.size = attachment.upload.size
                attachment.save()
                updated_attachments+=1
            except Exception:
                attachment_errors+=1
                pass

        self.stdout.write(f"updated size for {updated_attachments} files / {attachment_errors} errors")
