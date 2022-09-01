from django.core.management import BaseCommand

from core.lib import is_schema_public, tenant_schema
from user.models import User


class Command(BaseCommand):
    help = "One-time use script to schedule sending users to concierge"

    def handle(self, *args, **options):
        from concierge.tasks import sync_user

        if is_schema_public():
            return

        for user in User.objects.all():
            sync_user.delay(tenant_schema(), user.id)
