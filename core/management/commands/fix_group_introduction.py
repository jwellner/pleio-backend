import signal_disabler
from django.core.management.base import BaseCommand
from django.db import connection
from core import config
from core.models import Group
from core.models.draft_backup import DraftBackup
from core.utils.convert import draft_to_tiptap, is_tiptap

class Command(BaseCommand):
    help = 'Convert draft to tiptap json'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    @signal_disabler.disable()
    def handle(self, *args, **options):

        if connection.schema_name == 'public':
            return

        count_html = 0
        count_rich = 0
        count_skipped = 0

        groups = Group.objects.all()

        for item in groups:
            original_intro = DraftBackup.objects.filter(content_id=item.guid, property='introduction').first()

            if not original_intro:
                count_skipped+=1
                continue

            if is_tiptap(item.introduction):
                count_skipped+=1
                continue

            if not original_intro.is_html:
                item.introduction = draft_to_tiptap(original_intro.data)
                item.save()
                count_rich+=1

        self.stdout.write(f"Groups converted: [draft: {count_rich} | html: {count_html} | skipped: {count_skipped}]")
