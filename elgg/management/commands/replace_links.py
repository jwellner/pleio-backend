import re

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from core import config
from core.models import Group, Entity, Comment, Widget
from backend2 import settings
from elgg.models import (
    Instances, GuidMap, ElggSitesEntity
)
from elgg.helpers import ElggHelpers
from django_tenants.management.commands import InteractiveTenantOption

from django.db import connections, connection
from django.db import IntegrityError


class Command(InteractiveTenantOption, BaseCommand):
    help = 'Replace links after import'
    import_id = None
    helpers = None
    elgg_domain = None
    tenant_domain = None

    def get_elgg_from_options_or_interactive(self, **options):
        all_elgg_sites = Instances.objects.using("elgg_control").all()

        if not all_elgg_sites:
            raise CommandError("""There are no elgg sites in the control database check config""")

        if options.get('elgg'):
            elgg_database = options['elgg']
        else:
            while True:
                elgg_database = input("Enter elgg database ('?' to list databases): ")
                if elgg_database == '?':
                    print('\n'.join(["%s" % s.name for s in all_elgg_sites]))
                else:
                    break

        if elgg_database not in [s.name for s in all_elgg_sites]:
            raise CommandError("Invalid database, '%s'" % (elgg_database,))

        return Instances.objects.using("elgg_control").get(name=elgg_database)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--elgg', help='elgg database')
        parser.add_argument('--elgg_domain', help='elgg domain')

    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return

        self.elgg_domain = options.get("elgg_domain", None)

        elgg_instance = self.get_elgg_from_options_or_interactive(**options)
        tenant = self.get_tenant_from_options_or_interactive(**options)

        self.stdout.write("Import elgg database '%s' to tenant '%s'\n" % (elgg_instance.name, tenant.schema_name))

        self.import_id = "import_%s" % elgg_instance.name

        # Change connection to elgg site database
        elgg_database_settings = settings.DATABASES["elgg_control"]
        elgg_database_settings["id"] = self.import_id
        elgg_database_settings["NAME"] = elgg_instance.name
        connections.databases[self.import_id] = elgg_database_settings

        # Change default connection to tenant
        connection.set_tenant(tenant)

        self.helpers = ElggHelpers(self.import_id)

        if GuidMap.objects.count() == 0:
            self.stdout.write(f"Import not run for tenant {tenant.schema_name}. Exiting.")
            return False

        elgg_site = ElggSitesEntity.objects.using(self.import_id).first()

        if not self.elgg_domain:
            matches = re.findall(r'http(?:s)?\:\/\/(.+)\/', elgg_site.url)
            self.elgg_domain = matches[0]

        self.tenant_domain = tenant.get_primary_domain().domain

        if not self.elgg_domain:
            self.stdout.write(f"Unable to get elgg domain. Exiting.")
            return False

        if not self.tenant_domain:
            self.stdout.write(f"Unable to get primary tenant domain. Exiting.")
            return False

        self.stdout.write(f"Found elgg domain {self.elgg_domain} and tenant domain {self.tenant_domain}")

        self._replace_menu()
        self._replace_entity_description()
        self._replace_group_description()
        self._replace_comment_description()
        self._replace_widget_settings()

        # All done!
        self.stdout.write("\n>> Done!")

    def _replace_menu(self):
        self.stdout.write("\n>> Replace MENU links (1) ", ending="")

        menu_items = config.MENU
        for item in menu_items:
            if 'link' in item and item['link']:
                item['link'] = self._replace_links(item['link'])

            for child in item.get("children", []):
                if 'link' in child and child['link']:
                    child['link'] = self._replace_links(child['link'])

        config.MENU = menu_items
        self.stdout.write(".", ending="")

    def _replace_entity_description(self):
        entities = Entity.objects.all().select_subclasses()
        self.stdout.write("\n>> Replace Entity.(rich_)description (%i) " % entities.count(), ending="")

        for entity in entities:
            if hasattr(entity, 'rich_description'):
                rich_description = self._replace_links(entity.rich_description)
                description = self._replace_links(entity.description)

                if rich_description != entity.rich_description or description != entity.description:
                    entity.rich_description = rich_description
                    entity.description = description
                    entity.save()
                    self.stdout.write("*", ending="")
                else:
                    self.stdout.write(".", ending="")

    def _replace_group_description(self):
        groups = Group.objects.all()
        self.stdout.write("\n>> Replace Group.(rich_)description (%i) " % groups.count(), ending="")

        for group in groups:
            rich_description = self._replace_links(group.rich_description)
            description = self._replace_links(group.description)

            if rich_description != group.rich_description or description != group.description:
                group.rich_description = rich_description
                group.description = description
                group.save()
                self.stdout.write("*", ending="")
            else:
                self.stdout.write(".", ending="")

    def _replace_comment_description(self):
        comments = Comment.objects.all()
        self.stdout.write("\n>> Replace Comment.(rich_)description (%i) " % comments.count(), ending="")

        for comment in comments:
            rich_description = self._replace_links(comment.rich_description)
            description = self._replace_links(comment.rich_description)

            if rich_description != comment.rich_description or description != comment.description:
                comment.rich_description = rich_description
                comment.description = description
                comment.save()
                self.stdout.write("*", ending="")
            else:
                self.stdout.write(".", ending="")

    def _replace_widget_settings(self):
        widgets = Widget.objects.all()
        self.stdout.write("\n>> Replace Widget.settings (%i) " % widgets.count(), ending="")

        for widget in widgets:
            changed = False
            if widget.settings:
                for setting in widget.settings:
                    if 'value' in setting and isinstance(setting.get('value'), str):
                        new_value = self._replace_links(setting.get('value'))
                        if new_value != setting.get('value'):
                            setting['value'] = new_value
                            changed = True
                        
            if changed:
                widget.save()
                self.stdout.write("*", ending="")
            else:
                self.stdout.write(".", ending="")

    def _replace_links(self, text):
        # Testing: https://regex101.com/r/13zeJW/2

        matches = re.findall(rf'(((https:\/\/{re.escape(self.elgg_domain)})|(^|(?<=[ \"\n]))\/)[\w\-\/]*\/(view|download)\/([0-9]+)[\w\-\.\/\?\%]*)', text)

        for match in matches:
            link = match[0]
            new_link = link
            ids = re.findall(r'\/([0-9]+)', link)
            for id in ids:
                map_entity = GuidMap.objects.filter(id=id).first()
                if map_entity:
                    new_link = new_link.replace(str(id), str(map_entity.guid))

            if link != new_link:
                text = text.replace(link, new_link)

        # make all local links relative
        text = text.replace(f"https://{self.elgg_domain}/", "/")

        return text