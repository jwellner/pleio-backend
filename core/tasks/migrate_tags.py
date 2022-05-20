from django_tenants.utils import schema_context

from core.models import Tag, Entity, Group
from backend2 import celery_app as app
from core.models.tags import EntityTag


@app.task
def migrate_tags(schema_name):
    """Temporal task to schedule migration of tags to the new system."""
    with schema_context(schema_name):
        for instance in Entity.objects.all():
            do_migrate_tags(instance)

        for instance in Group.objects.all():
            do_migrate_tags(instance)


def do_migrate_tags(instance):
    # pylint: disable=protected-access
    instance.tags = instance._tag_summary
    new_summary = Tag.translate_tags(instance._tag_summary)
    instance.__class__.objects.filter(id=instance.id).update(_tag_summary=[t for t in new_summary])


@app.task
def revert_tags(schema_name):
    """Temporal task to schedule undo the migration of tags to the new system."""
    with schema_context(schema_name):
        for instance in Entity.objects.all():
            copy_tags_back_to_tag_field(instance)

        for instance in Group.objects.all():
            copy_tags_back_to_tag_field(instance)


def copy_tags_back_to_tag_field(instance):
    # pylint: disable=protected-access
    if len(instance._tag_summary) > 0 and len(instance.tags) > 0:
        original_tags = [et.author_label for et in EntityTag.objects.filter(entity_id=instance.id)]
        instance.__class__.objects.filter(id=instance.id).update(_tag_summary=original_tags)
