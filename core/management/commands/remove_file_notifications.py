import signal_disabler
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Update widget sorting to timePublished'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @signal_disabler.disable()
    def handle(self, *args, **options):

        if connection.schema_name == 'public':
            return

        file_content_type_id = ContentType.objects.get(model='filefolder').id

        notifications = Notification.objects.filter(action_object_content_type_id=file_content_type_id)
        notifications_count = notifications.count()
        notifications.delete()


        self.stdout.write(f"deleted {notifications_count} file notifications")
