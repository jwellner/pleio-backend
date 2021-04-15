import json
import re
import signal_disabler
from collections import Counter
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone, dateformat, formats
from django.utils.translation import ugettext_lazy
from django.conf import settings
from core import config
from core.models import Entity, EntityView
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

        self.count_file_access_fixed = 0

        def _validate_access(file, group):
            # fix read_access
            group_access = ACCESS_TYPE.group.format(group.id)
            read_access = list(file.read_access)

            # use for adding group if some rights are removed
            read_access_removed = False
            try:
                read_access.remove(ACCESS_TYPE.logged_in)
                read_access_removed = True
            except Exception:
                pass
            try:
                read_access.remove(ACCESS_TYPE.public)
                read_access_removed = True
            except Exception:
                pass
            if read_access_removed:
                read_access.append(group_access)
                read_access = list(set(read_access))

            write_access = list(file.write_access)

            # use for adding group if some rights are removed
            write_access_removed = False
            try:
                write_access.remove(ACCESS_TYPE.logged_in)
                write_access = True
            except Exception:
                pass
            try:
                write_access.remove(ACCESS_TYPE.public)
                write_access = True
            except Exception:
                pass
            if write_access_removed:
                write_access.append(group_access)
                write_access = list(set(write_access))

            if (set(write_access) == set(file.write_access)) and (set(read_access) == set(file.read_access)):
                return

            file.read_access = read_access
            file.write_access = write_access
            file.save()
            self.count_file_access_fixed += 1
            self.stdout.write(file.guid)

        def _set_file_access(text, entity):
                matches = re.findall(
                    rf'(((https:\/\/{re.escape(tenant_domain)})|(^|(?<=[ \"\n])))\/file\/download\/([\w\-]+))',
                    text
                )

                for match in matches:
                    file_id = match[4]
                    file_entity = None
                    # try old elgg id
                    try:
                        has_file = GuidMap.objects.filter(id=file_id, object_type="file").first()
                        if has_file:
                            file_entity = FileFolder.objects.get(id=has_file.guid)
                    except Exception:
                        pass

                    # try new uuid
                    try:
                        file_entity = FileFolder.objects.get(id=file_id)
                    except Exception:
                        pass

                    if file_entity:
                        _validate_access(file_entity, entity.group)

        def _set_file_access_rich_description_json(entity):
            if hasattr(entity, 'rich_description'):
                try:
                    data = json.loads(entity.rich_description)
                    for idx in data["entityMap"]:
                        # only search in DOCUMENT
                        if data["entityMap"][idx]["type"] in ["DOCUMENT"]:
                            if "url" in data["entityMap"][idx]["data"]:
                                _set_file_access(data["entityMap"][idx]["data"]["url"], entity)
                            if "href" in data["entityMap"][idx]["data"]:
                                _set_file_access(data["entityMap"][idx]["data"]["href"], entity)
                except Exception:
                    pass

        # -- fix access of files in content of closed groups

        entities = Entity.objects.filter(group__is_closed=True).select_subclasses()

        self.stdout.write(f"start checking access of files in {entities.count()} groups")

        for entity in entities:
            if hasattr(entity, 'rich_description'):
                _set_file_access_rich_description_json(entity)

        self.stdout.write(f"fixed access of {self.count_file_access_fixed} files in content, in closed groups")