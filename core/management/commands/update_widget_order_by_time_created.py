from core.models.comment import CommentMixin
import signal_disabler
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from django.db import connection
from core.models import Widget


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

        updated_widgets = 0

        widgets = Widget.objects.filter(type__in=["objects", "activity"])
        for widget in widgets:
            changed = False
            for setting in widget.settings:
                if setting.get("key", None) == "sortBy" and setting.get("value", "").startswith("timeCreated"):

                    withOrder = setting.get("value").split("-")
                    setting["value"] = "timePublished"
                    if len(withOrder) > 1:
                        setting["value"] += "-" + withOrder[1]

                    changed = True
                    updated_widgets+=1

            if changed:
                widget.save()

        self.stdout.write(f"updated sortBy to timePublished for {updated_widgets} widgets")
