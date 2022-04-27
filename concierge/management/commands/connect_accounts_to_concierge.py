from django.core.management import BaseCommand
from django_tenants.utils import tenant_context
from django.db import connection

from tenants.models import Client
from user.models import User


class Command(BaseCommand):
    help = "Schedule sending users to concierge"

    def handle(self, *args, **options):
        from concierge.tasks import sync_user

        if connection.schema_name == 'public':
            return

        for user in User.objects.all():
            sync_user.delay(connection.schema_name, user.id)
