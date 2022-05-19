from django.core.management import BaseCommand
from django_tenants.utils import schema_context

from core.models import Entity, Group
from core.models.tags import EntityTag, Tag
from tenants.models import Client


class Command(BaseCommand):
    help = 'Cleanup deleted users'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('-r', '--revert', default=False, action='store_true', help="Undo the tag migration")

    def handle(self, *args, **options):
        for client in Client.objects.exclude(name='public'):
            self.stdout.write("\nProcessing %s (schema=%s)..." % (client.name, client.schema_name))
            with schema_context(client.schema_name):
                if not options['revert']:
                    self.migrate()
                else:
                    self.revert()
        self.stdout.write("\nCompleted!")

    def migrate(self):
        for instance in Entity.objects.all():
            self.migrate_tags(instance)

        for instance in Group.objects.all():
            self.migrate_tags(instance)

    def migrate_tags(self, instance):
        self.stdout.write(".", ending="")
        # pylint: disable=protected-access
        instance.tags = instance._tag_summary
        new_summary = Tag.translate_tags(instance._tag_summary)
        instance.__class__.objects.filter(id=instance.id).update(_tag_summary=[t for t in new_summary])

    def revert(self):
        for instance in Entity.objects.all():
            self.copy_tags_back_to_tag_field(instance)

        for instance in Group.objects.all():
            self.copy_tags_back_to_tag_field(instance)

    def copy_tags_back_to_tag_field(self, instance):
        # pylint: disable=protected-access
        if len(instance._tag_summary) > 0 and len(instance.tags) > 0:
            self.stdout.write(".", ending="")
            original_tags = [et.author_label for et in EntityTag.objects.filter(entity_id=instance.id)]
            instance.__class__.objects.filter(id=instance.id).update(_tag_summary=original_tags)
