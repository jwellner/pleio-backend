import signal_disabler
from django.core.management.base import BaseCommand
from django.db import connection
from core.models import UserProfileField


class Command(BaseCommand):
    help = 'Remove duplicate user profile fields'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @signal_disabler.disable()
    def handle(self, *args, **options):

        if connection.schema_name == 'public':
            return

        count = 0

        dupes = UserProfileField.objects.all().difference(UserProfileField.objects.distinct('user_profile', 'profile_field'))

        for dupe in dupes:
            last = UserProfileField.objects.filter(user_profile=dupe.user_profile, profile_field=dupe.profile_field).last()
            UserProfileField.objects.filter(user_profile=dupe.user_profile, profile_field=dupe.profile_field).exclude(id=last.id).delete()
            count+=1

        self.stdout.write(f"Removed {count} duplicate profile fields")


