from core.models.comment import CommentMixin
import json
import re
import signal_disabler
from datetime import datetime
from django.core.management.base import BaseCommand
from user.models import User
from django.db import connection


class Command(BaseCommand):
    help = 'Cleanup deleted users'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @signal_disabler.disable()
    def handle(self, *args, **options):

        if connection.schema_name == 'public':
            return

        cleanup = 0

        deleted_users = User.objects.with_deleted().filter(is_active=False, name="Verwijderde gebruiker")
        for user in deleted_users:
            user.delete()
            cleanup+=1

        self.stdout.write(f"cleaned up data for {cleanup} deleted users")