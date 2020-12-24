import html

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from core import config
from core.lib import tenant_schema, access_id_to_acl
from tenants.models import Client
from core.models import Entity, Group
from backend2 import settings


class Command(BaseCommand):
    help = 'Fix html encoded strings in title and description'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return

        # check if command is run with tenant
        schema = tenant_schema()

        if schema == 'public':
            self.stdout.write("Don't run on public schema\n")
            return

        self._fix_html_encode()

        # All done!
        self.stdout.write(">> Done!\n\n")

    def _fix_html_encode(self):
        i = 0
        entities = Entity.objects.all().select_subclasses()
        for e in entities:
            changed = False
            if hasattr(e, 'title'):
                title = html.unescape(e.title)
                if title != e.title:
                    e.title = title
                    changed = True
            if hasattr(e, 'description'):
                description = html.unescape(e.description)
                if description != e.description:
                    e.description = description
                    changed = True

            if changed:
                i+=1
                e.save()

        self.stdout.write("\n>> Updated " + str(i) + " entities.")

        i = 0
        groups = Group.objects.all()
        for g in groups:
            name = html.unescape(g.name)
            description = html.unescape(g.description)
            if g.name != name or g.description != description:
                g.name = name
                g.description = description
                g.save()
                i+=1
        self.stdout.write("\n>> Updated " + str(i) + " groups.")
