import json
import re
import signal_disabler
import os
from collections import Counter
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone, dateformat, formats
from django.utils.translation import ugettext_lazy
from django.conf import settings
from core import config
from core.models import Entity, Attachment, Comment, Group
from datetime import datetime, timedelta
from django.db import connection
from tenants.models import Client
from user.models import User
from file.models import FileFolder
from core.tasks import send_mail_multi
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from core.constances import ACCESS_TYPE


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

        tenant = Client.objects.get(schema_name=connection.schema_name)
        tenant_domain = tenant.get_primary_domain().domain

        self.count_file_convert = 0
        self.files_to_delete = []

        def _convert_file(text, entity):
                match = re.match(
                    rf'(((https://{re.escape(tenant_domain)})|^)/file/download/([\w\-]+))',
                    text
                )

                if match:
                    file_id = match.group(4)
                    file_entity = None
                    try:
                        file_entity = FileFolder.objects.get(id=file_id)

                        if not file_entity.group:
                            attachment = Attachment.objects.create(
                                mime_type=file_entity.mime_type,
                                attached=entity
                            )
                            url = entity.url

                            old_file = file_entity.upload.open()
                            attachment.upload.save(os.path.basename(file_entity.upload.name), old_file)

                            print(f"{file_entity.url} in {url} to {attachment.url}")

                            # delete after finised (it may be possible files are used multiple times ?)
                            self.files_to_delete.append(file_entity.id)

                            self.count_file_convert += 1

                            return attachment.url
                    except Exception as e:
                        print(f"Error converting file: {e}")
                        pass

                return text


        def _convert_files_rich_description_json(obj):
            try:
                data = json.loads(obj.rich_description)
                for idx in data["entityMap"]:
                    # only search in DOCUMENT
                    if data["entityMap"][idx]["type"] in ["DOCUMENT", "IMAGE"]:
                        for t in ["url", "href", "src"]:
                            if t in data["entityMap"][idx]["data"]:
                                data["entityMap"][idx]["data"][t] = _convert_file(data["entityMap"][idx]["data"][t], entity)

                rich_description = json.dumps(data)

                if not obj.rich_description == rich_description:
                    obj.rich_description = rich_description
                    obj.save()

            except Exception:
                pass

        def _convert_files_introduction_json(obj):
            try:
                data = json.loads(obj.introduction)
                for idx in data["entityMap"]:
                    # only search in DOCUMENT
                    if data["entityMap"][idx]["type"] in ["DOCUMENT", "IMAGE"]:
                        for t in ["url", "href", "src"]:
                            if t in data["entityMap"][idx]["data"]:
                                data["entityMap"][idx]["data"][t] = _convert_file(data["entityMap"][idx]["data"][t], entity)

                introduction = json.dumps(data)

                if not obj.introduction == introduction:
                    obj.introduction = introduction
                    obj.save()

            except Exception:
                pass

        entities = Entity.allObjects.all().select_subclasses()

        self.stdout.write(f"Start checking {entities.count()} entities")

        for entity in entities:
            _convert_files_rich_description_json(entity)

        comments = Comment.objects.all()

        self.stdout.write(f"Start checking {comments.count()} comments")

        for comment in comments:
            _convert_files_rich_description_json(comment)

        groups = Group.objects.all()

        self.stdout.write(f"Start checking {groups.count()} groups")

        for group in groups:
            _convert_files_rich_description_json(group)
            _convert_files_introduction_json(group)

        self.stdout.write(f"Converted {self.count_file_convert} files to attachment")

        # make file list unique
        self.files_to_delete = list(set(self.files_to_delete))

        self.stdout.write(f"Start deleting {len(self.files_to_delete)} old files")
        for f in self.files_to_delete:
            file = FileFolder.objects.get(id=f)
            file.delete()
        self.stdout.write(f"Done!")
