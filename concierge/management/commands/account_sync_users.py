from django.core.management import BaseCommand

from core.lib import tenant_schema
from user.models import User


class Command(BaseCommand):
    help = "Script to schedule update profile data from account"

    def handle(self, *args, **options):
        from concierge.tasks import profile_updated_signal
        for user_id in User.objects.filter(external_id__isnull=False).values_list('id', flat=True):
            profile_updated_signal.delay(tenant_schema(), str(user_id))
