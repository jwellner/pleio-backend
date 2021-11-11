from core.models.comment import CommentMixin
import json
import re
import signal_disabler
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import connection
from core import config
from core.models import Entity, Comment, CommentRequest, Group, Widget, UserProfileField
from core.models.draft_backup import DraftBackup
from core.utils.convert import draft_to_tiptap, is_tiptap
from core.utils.html_to_draftjs import html_to_draftjs

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

        original_login_intro = DraftBackup.objects.filter(content_id=0, property='LOGIN_INTRO').first()
        original_onboarding_intro = DraftBackup.objects.filter(content_id=0, property='ONBOARDING_INTRO').first()

        if not original_login_intro:
            if is_tiptap(config.LOGIN_INTRO):
                count_skipped+=1
            else:
                original_login_intro = DraftBackup()
                original_login_intro.content_id = 0
                original_login_intro.property = 'LOGIN_INTRO'
                original_login_intro.data = config.LOGIN_INTRO
                original_login_intro.save()

        config.LOGIN_INTRO = draft_to_tiptap(original_login_intro.data)
        count_rich+=1

        if not original_onboarding_intro:
            if is_tiptap(config.ONBOARDING_INTRO):
                count_skipped+=1
            else:
                original_onboarding_intro = DraftBackup()
                original_onboarding_intro.content_id = 0
                original_onboarding_intro.property = 'ONBOARDING_INTRO'
                original_onboarding_intro.data = config.ONBOARDING_INTRO
                original_onboarding_intro.save()

        config.ONBOARDING_INTRO = draft_to_tiptap(original_onboarding_intro.data)
        count_rich+=1

        self.stdout.write(f"Config: [draft: {count_rich} | html: {count_html} | skipped: {count_skipped}]")

        count_html = 0
        count_rich = 0
        count_skipped = 0

        entities = Entity.objects.all().select_subclasses()
        for item in entities:
            if not hasattr(item, 'rich_description'):
                continue

            original = DraftBackup.objects.filter(content_id=item.guid, property='rich_description').first()

            if not original:
                if is_tiptap(item.rich_description):
                    count_skipped+=1
                    continue

                original = DraftBackup()
                original.content_id = item.guid
                original.property = 'rich_description'
                if item.rich_description:
                    original.data = item.rich_description
                else:
                    original.data = item.description
                    original.is_html = True

                original.save()

            # use original to convert to TipTap if is_html make JSON string!
            if not original.is_html:
                item.rich_description = draft_to_tiptap(original.data)
                count_rich+=1
            else:
                draft_string = json.dumps(html_to_draftjs(original.data))
                item.rich_description = draft_to_tiptap(draft_string)
                count_html+=1
            item.save()

        self.stdout.write(f"Entities converted: [draft: {count_rich} | html: {count_html} | skipped: {count_skipped}]")

        count_html = 0
        count_rich = 0
        count_skipped = 0

        comments = Comment.objects.all()

        for item in comments:
            original = DraftBackup.objects.filter(content_id=item.guid, property='rich_description').first()

            if not original:
                if is_tiptap(item.rich_description):
                    count_skipped+=1
                    continue

                original = DraftBackup()
                original.content_id = item.guid
                original.property = 'rich_description'
                if item.rich_description:
                    original.data = item.rich_description
                else:
                    original.data = item.description
                    original.is_html = True

                original.save()

            # use original to convert to TipTap if is_html make JSON string!
            if not original.is_html:
                item.rich_description = draft_to_tiptap(original.data)
                count_rich+=1
            else:
                draft_string = json.dumps(html_to_draftjs(original.data))
                item.rich_description = draft_to_tiptap(draft_string)
                count_html+=1
            item.save()

        self.stdout.write(f"Comments converted: [draft: {count_rich} | html: {count_html} | skipped: {count_skipped}]")

        count_html = 0
        count_rich = 0
        count_skipped = 0

        comment_requests = CommentRequest.objects.all()

        for item in comment_requests:
            original = DraftBackup.objects.filter(content_id=item.guid, property='rich_description').first()

            if not original:
                if is_tiptap(item.rich_description):
                    count_skipped+=1
                    continue

                original = DraftBackup()
                original.content_id = item.guid
                original.property = 'rich_description'
                original.data = item.rich_description
                original.save()

            # use original to convert to TipTap if is_html make JSON string!
            item.rich_description = draft_to_tiptap(original.data)
            count_rich+=1

            item.save()

        self.stdout.write(f"CommentsRequests converted: [draft: {count_rich} | html: {count_html} | skipped: {count_skipped}]")

        count_html = 0
        count_rich = 0
        count_skipped = 0

        groups = Group.objects.all()

        for item in groups:
            original_rich = DraftBackup.objects.filter(content_id=item.guid, property='rich_description').first()
            original_intro = DraftBackup.objects.filter(content_id=item.guid, property='introduction').first()

            if not original_rich:
                if is_tiptap(item.rich_description):
                    count_skipped+=1
                    continue

                original_rich = DraftBackup()
                original_rich.content_id = item.guid
                original_rich.property = 'rich_description'
                if item.rich_description:
                    original_rich.data = item.rich_description
                else:
                    original_rich.data = item.description
                    original_rich.is_html = True

                original_rich.save()

            # use original to convert to TipTap if is_html make JSON string!
            if not original_rich.is_html:
                item.rich_description = draft_to_tiptap(original_rich.data)
                count_rich+=1
            else:
                draft_string = json.dumps(html_to_draftjs(original.data))
                item.rich_description = draft_to_tiptap(draft_string)
                count_html+=1
            item.save()

            if not original_intro:
                if is_tiptap(item.introduction):
                    count_skipped+=1
                    continue

                original_intro = DraftBackup()
                original_intro.content_id = item.guid
                original_intro.property = 'introduction'
                #TODO: detect if introduction is HTML... (json parse?)
                original_intro.data = item.introduction
                original_intro.save()

            # use original to convert to TipTap if is_html make JSON string!
            if not original_intro.is_html:
                item.introduction = draft_to_tiptap(original_intro.data)
                count_rich+=1
            else:
                item.introduction = draft_to_tiptap(html_to_draftjs(original_intro.data))
                count_html+=1
            item.save()

        self.stdout.write(f"Groups converted: [draft: {count_rich} | html: {count_html} | skipped: {count_skipped}]")

        count_html = 0
        count_rich = 0
        count_skipped = 0

        widgets = Widget.objects.filter(type="text").all()

        for widget in widgets:
            updated = False

            for setting in widget.settings:
                if setting.get("key", None) == "richDescription":
                    original = DraftBackup.objects.filter(content_id=widget.guid, property='richDescription').first()

                    if not original:
                        if is_tiptap(setting["value"]):
                            count_skipped+=1
                            continue

                        original = DraftBackup()
                        original.content_id = widget.guid
                        original.property = 'richDescription'
                        original.data = setting["value"]
                        original.save()

                    setting["value"] = draft_to_tiptap(original.data)
                    count_rich+=1
                    updated = True

            if updated:
                widget.save()

        self.stdout.write(f"Widgets converted: [draft: {count_rich} | html: {count_html} | skipped: {count_skipped}]")

        count_html = 0
        count_rich = 0
        count_skipped = 0

        profile_fields = UserProfileField.objects.filter(profile_field__field_type="html_field").all()

        for field in profile_fields:

            original = DraftBackup.objects.filter(content_id=field.id, property='value').first()

            if not original:
                if is_tiptap(field.value):
                    count_skipped+=1
                    continue

                original = DraftBackup()
                original.content_id = field.id
                original.property = 'value'
                original.data = field.value
                original.save()

            field.value = draft_to_tiptap(original.data)
            field.save()
            count_rich+=1

        self.stdout.write(f"UserProfileField converted: [draft: {count_rich} | html: {count_html} | skipped: {count_skipped}]")