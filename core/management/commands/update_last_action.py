from core.models.comment import CommentMixin
import json
import re
import signal_disabler
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from core.models import Entity
from django.db import connection
from tenants.models import Client


class Command(BaseCommand):
    help = 'Check access of files uploaded in content'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @signal_disabler.disable()
    def handle(self, *args, **options):

        if connection.schema_name == 'public':
            return

        tenant = Client.objects.get(schema_name=connection.schema_name)
        tenant_domain = tenant.get_primary_domain().domain

        updated_entities = 0

        for subclass in CommentMixin.__subclasses__():
            entities = subclass.objects.annotate(cnt=Count('comments')).filter(cnt__gt=0)
            for entity in entities:
                latest_comment = entity.comments.first()
                entity.last_action = latest_comment.created_at
                entity.save()
                updated_entities+=1


        self.stdout.write(f"updated last_action for {updated_entities} entities")