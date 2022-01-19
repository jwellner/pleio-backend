from core.models.comment import CommentMixin
import json
import re
import signal_disabler
from django.core.management.base import BaseCommand
from django.db.models import F, Count, CharField, Value
from django.db.models.functions import Concat
from django.db import connection
from notifications.models import Notification
from user.models import User
from core.models import ResizedImage


class Command(BaseCommand):
    help = 'Remove duplicate resized images'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @signal_disabler.disable()
    def handle(self, *args, **options):

        if connection.schema_name == 'public':
            return

        count = 0

        qs = ResizedImage.objects.annotate(
                dupe_id=Concat(
                            F('original_object_id')
                            , Value('#')
                            , F('size')
                            , output_field=CharField()
                )
            )

        dupes = qs.values('dupe_id').annotate(dupe_count=Count('dupe_id')).filter(dupe_count__gt=1)

        for dupe in dupes:
            id, size = dupe['dupe_id'].split('#')
            
            for image in ResizedImage.objects.filter(original_object_id=id, size=size)[1:]:
                image.delete()
                count+=1

        self.stdout.write(f"Removed {count} duplicate images")


