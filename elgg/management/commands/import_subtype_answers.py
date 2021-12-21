from core.models.entity import EntityView
import html
import signal_disabler
from datetime import datetime
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from core import config
from core.models import Group, Entity, Comment, Widget
from backend2 import settings
from elgg.models import (
    Instances, GuidMap, ElggUsersEntity, ElggMetastrings, ElggEntities, FriendlyUrlMap, ElggMetadata, ElggObjectsEntity
)
from question.models import Question
from elgg.helpers import ElggHelpers
from django_tenants.management.commands import InteractiveTenantOption
from django_tenants.utils import schema_context
from tenants.models import Client, Domain

from django.db import connections, connection
from django.db import IntegrityError
from core.lib import tenant_schema


class Command(InteractiveTenantOption, BaseCommand):
    help = 'Add answers to content types'
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

    @signal_disabler.disable()
    def handle(self, *args, **options):
        if not settings.RUN_AS_ADMIN_APP:
            self.stdout.write("Only run this command from admin instance.")
            return

        self.added_answers = 0

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

        self.helpers = ElggHelpers(self.import_id)

        elgg_answers_items = ElggObjectsEntity.objects.using(self.import_id).filter(entity__subtype__subtype='answer')

        self.stdout.write("\n>> Answers (%i) " % elgg_answers_items.count(), ending="")

        self.tenant_domain = tenant.get_primary_domain().domain

        self.stdout.write(f"Found elgg and tenant domain for {self.tenant_domain}")

        with schema_context(tenant.schema_name):
            for elgg_answer in elgg_answers_items:
                try:
                    question_id = GuidMap.objects.filter(id=elgg_answer.entity.container_guid, object_type='question').first().guid
                    question = Question.objects.get(id=question_id)

                    if GuidMap.objects.filter(id=elgg_answer.entity.guid, object_type='answer').exists():
                        self.stdout.write("x", ending="")
                        continue

                    hasComment = question.comments.filter(description=html.unescape(elgg_answer.description)).first()
                    if hasComment:
                        self.stdout.write("X", ending="")
                        # add mapping for future references
                        GuidMap.objects.create(id=elgg_answer.entity.guid, guid=hasComment.guid, object_type='answer')
                        continue

                    comment = Comment()
                    comment.description = html.unescape(elgg_answer.description)
                    comment.rich_description = elgg_answer.entity.get_metadata_value_by_name("richDescription")
                    comment.owner = self.helpers.get_user_or_admin(elgg_answer.entity.owner_guid)
                    comment.created_at = datetime.fromtimestamp(elgg_answer.entity.time_created, tz="Europe/Amsterdam")
                    comment.updated_at = datetime.fromtimestamp(elgg_answer.entity.time_updated, tz="Europe/Amsterdam")
                    comment.container = question
                    comment.save()

                    self.helpers.save_entity_annotations(elgg_answer, comment, ["vote"])

                    # add mapping for future references
                    GuidMap.objects.create(id=elgg_answer.entity.guid, guid=comment.guid, object_type='answer')

                    self.added_answers = self.added_answers + 1
                    self.stdout.write(".", ending="")
                except Exception:
                    pass

        self.stdout.write(f"Done importing answers, {self.added_answers} answers added")
