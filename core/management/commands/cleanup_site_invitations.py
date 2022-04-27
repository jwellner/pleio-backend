from django.core.management import BaseCommand
from django.db import connection

from core.models import SiteInvitation
from user.models import User


class Command(BaseCommand):
    help = 'Cleanup not yet unflagged site invitations'

    def execute(self, *args, **options):
        if connection.schema_name == 'public':
            return

        for invitation in SiteInvitation.objects.all():
            if User.objects.filter(email=invitation.email, last_login__isnull=False).exists():
                invitation.delete()


