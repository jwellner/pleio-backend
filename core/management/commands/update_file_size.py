from core.models.comment import CommentMixin
import json
import re
import signal_disabler
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from django.db import connection
from file.models import FileFolder


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

        updated_files = 0
        file_errors = 0

        files = FileFolder.objects.filter(is_folder=False)
        for file in files:
            try:
                file.size = file.upload.size
                updated_files+=1
            except Exception:
                file_errors+=1
                pass

        self.stdout.write(f"updated size for {updated_files} files / {file_errors} errors")
