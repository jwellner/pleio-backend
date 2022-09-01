import signal_disabler

from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import Entity
from core.lib import ACCESS_TYPE, is_schema_public
from django.db import connection


class Command(BaseCommand):
    help = 'Update entities with public ACL to logged_in'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def handle(self, *args, **options):

        if is_schema_public():
            return

        updated = 0

        filters = Q()
        filters.add(Q(read_access__overlap=list([ACCESS_TYPE.public])), Q.OR)
        filters.add(Q(write_access__overlap=list([ACCESS_TYPE.public])), Q.OR)

        public_entities = Entity.objects.filter(filters)

        for entity in public_entities:
            if ACCESS_TYPE.public in entity.read_access:
                entity.read_access.remove(ACCESS_TYPE.public)
                entity.read_access.append(ACCESS_TYPE.logged_in)

            if ACCESS_TYPE.public in entity.write_access:
                entity.write_access.remove(ACCESS_TYPE.public)
                entity.write_access.append(ACCESS_TYPE.logged_in)

            with signal_disabler.disable():
                entity.save()
            updated += 1


        self.stdout.write(f"Updated acl for {updated} entities")