from core.models.comment import CommentMixin
import json
import re
import signal_disabler
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import UserProfileField
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

        updated_dates = 0

        fields = UserProfileField.objects.filter(profile_field__field_type='date_field', value_date=None)
        for field in fields:
            try:
                field.value_date = datetime.strptime(field.value, '%Y-%m-%d')
                field.save()
                updated_dates+=1
            except Exception:
                pass

        self.stdout.write(f"updated value_date for {updated_dates} profile fields")