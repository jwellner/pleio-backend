from core.models.comment import CommentMixin
import json
import re
import signal_disabler
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from django.db import connection
from notifications.models import Notification
from user.models import User
from core.models import Entity


class Command(BaseCommand):
    help = 'Fixes notification action_object_content_type_id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @signal_disabler.disable()
    def handle(self, *args, **options):

        if connection.schema_name == 'public':
            return

        deleted_notifs = 0
        updated_notifs = 0

        notifs = Notification.objects.filter(verb='welcome', action_object_content_type_id=None)
        for n in notifs:
            n.action_object = n.actor
            n.save()
            updated_notifs+=1

        notifs = Notification.objects.filter(action_object_content_type_id=None)
        for n in notifs:
            entity = Entity.objects.filter(id=n.action_object_object_id).select_subclasses().first()
            if entity:
                n.action_object = entity
                n.save()
                updated_notifs+=1
            else:
                n.delete()
                deleted_notifs+=1
        
        self.stdout.write(f"Fixed {updated_notifs} notifications, deleted {deleted_notifs} notifications")
