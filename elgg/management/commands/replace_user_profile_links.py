import re
import json

from django.core import management
from django.core.management.base import BaseCommand, CommandError
from core import config
from core.models import Group, Entity, Comment, Widget
from backend2 import settings
from elgg.models import (
    Instances, GuidMap, ElggUsersEntity
)
from elgg.helpers import ElggHelpers
from django_tenants.management.commands import InteractiveTenantOption
from django_tenants.utils import schema_context
from tenants.models import Client, Domain

from django.db import connections, connection
from django.db import IntegrityError
from core.lib import tenant_schema


class Command(InteractiveTenantOption, BaseCommand):
    help = 'Replace user profile links after import'
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

        self.replaced_profile_link_count = 0

        self.elgg_domain = options.get("elgg_domain", None)

        elgg_instance = self.get_elgg_from_options_or_interactive(**options)
        tenant = self.get_tenant_from_options_or_interactive(**options)

        self.stdout.write("Import elgg database '%s' to tenant '%s'\n" % (elgg_instance.name, tenant.schema_name))

        self.import_id = "import_%s" % elgg_instance.name
        # Change connection to elgg site database
        elgg_database_settings = settings.DATABASES["elgg_control"].copy()
        elgg_database_settings["id"] = self.import_id
        elgg_database_settings["NAME"] = elgg_instance.name
        connections.databases[self.import_id] = elgg_database_settings

        # Change default connection to tenant
        connection.set_tenant(tenant)

        elgg_users = ElggUsersEntity.objects.using(self.import_id)

        self.tenant_domain = tenant.get_primary_domain().domain

        self.stdout.write(f"Found elgg and tenant domain for {self.tenant_domain}")

        usernames = {}
        for user in elgg_users:
            usernames[user.username] = user.entity.guid


        with schema_context(tenant.schema_name):
            # TODO: Disable updated_at

            tenant = Client.objects.get(schema_name=tenant.schema_name)
            tenant_domain = tenant.get_primary_domain().domain

            def _replace_user_profile_links(text):
                # match links where old username is replaced with guid
                matches1 = re.findall(r'((^|(?<=[ \"\n]))\/user\/([\w\.-]+)\/profile)', text)
                matches2 = re.findall(r'((^|(?<=[ \"\n]))\/profile\/([\w\.-]+))', text)

                matches = matches1 + matches2

                for match in matches:
                    link = match[0]
                    new_link = link
                    username = match[2]

                    if username not in usernames:
                        continue
                    guid = usernames[username]

                    map_entity = GuidMap.objects.filter(id=guid).first()

                    if map_entity:
                        new_link = f'/user/{str(map_entity.guid)}/profile'
                        if link != new_link:
                            text = text.replace(link, new_link)
                            self.replaced_profile_link_count = self.replaced_profile_link_count + 1
                return text


            def _replace_rich_description_json(rich_description):
                if rich_description:
                    try:
                        data = json.loads(rich_description)
                        for idx in data["entityMap"]:
                            if data["entityMap"][idx]["type"] == "IMAGE":
                                data["entityMap"][idx]["data"]["src"] = _replace_user_profile_links(data["entityMap"][idx]["data"]["src"])
                            if data["entityMap"][idx]["type"] in ["LINK", "DOCUMENT"]:
                                if "url" in data["entityMap"][idx]["data"]:
                                    data["entityMap"][idx]["data"]["url"] = _replace_user_profile_links(data["entityMap"][idx]["data"]["url"])
                                if "href" in data["entityMap"][idx]["data"]:
                                    data["entityMap"][idx]["data"]["href"] = _replace_user_profile_links(data["entityMap"][idx]["data"]["href"])
                        return json.dumps(data)
                    except Exception:
                        pass
                return rich_description

            self.stdout.write("Start replace user profile links")

            # -- Replace entity descriptions
            entities = Entity.objects.all().select_subclasses()

            for entity in entities:
                if hasattr(entity, 'rich_description'):
                    rich_description = _replace_rich_description_json(entity.rich_description)
                    description = _replace_user_profile_links(entity.description)

                    if rich_description != entity.rich_description or description != entity.description:
                        entity.rich_description = rich_description
                        entity.description = description
                        entity.save()

            # -- Replace group descriptions
            groups = Group.objects.all()

            for group in groups:
                rich_description = _replace_rich_description_json(group.rich_description)
                description = _replace_user_profile_links(group.description)

                try:
                    introduction = json.loads(group.introduction)
                    introduction = _replace_rich_description_json(group.introduction)
                except Exception:
                    # old elgg sites dont have draftjs json
                    introduction = _replace_user_profile_links(group.description)

                try:
                    welcome_message = json.loads(group.welcome_message)
                    welcome_message = _replace_rich_description_json(group.welcome_message)
                except Exception:
                    # old elgg sites dont have draftjs json
                    welcome_message = _replace_user_profile_links(group.welcome_message)

                if rich_description != group.rich_description or \
                    description != group.description or \
                    introduction != group.introduction or \
                    welcome_message != group.welcome_message:

                    group.rich_description = rich_description
                    group.description = description
                    group.introduction = introduction
                    group.welcome_message = welcome_message
                    group.save()

            # -- Replace widget settings
            widgets = Widget.objects.all()

            for widget in widgets:
                changed = False
                if widget.settings:
                    for setting in widget.settings:
                        if 'value' in setting and isinstance(setting.get('value'), str):
                            new_value = _replace_user_profile_links(setting.get('value'))
                            if new_value != setting.get('value'):
                                setting['value'] = new_value
                                changed = True

                if changed:
                    widget.save()


            self.stdout.write(f"Done replacing user profile links, {self.replaced_profile_link_count} links replaced")
