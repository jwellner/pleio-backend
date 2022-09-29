from ariadne import ObjectType

from core.lib import str_to_datetime
from core.models import Group
from core.utils.entity import load_entity_by_id
from user.models import User

revision = ObjectType("Revision")


@revision.field('timeCreated')
def resolve_revsion_time_created(obj, info):
    # pylint: disable=unused-argument
    return obj.created_at


@revision.field('changedFields')
def resolve_changed_fields(obj, info):
    # pylint: disable=unused-argument
    return [str(key) for key in obj.content.keys()]


@revision.field('content')
def resolve_content(obj, info):
    # pylint: disable=unused-argument
    content = {}
    content.update(obj.unchanged)
    content.update(obj.content)
    return content


@revision.field('type')
def resolve_type(obj, info):
    # pylint: disable=unused-argument
    return "update" if obj.is_update else "create"


content_version = ObjectType('ContentVersion')


@content_version.field("timeCreated")
def resolve_time_created(obj, info):
    # pylint: disable=unused-argument
    return str_to_datetime(obj.get('timeCreated'))


@content_version.field("timePublished")
def resolve_time_published(obj, info):
    # pylint: disable=unused-argument
    return str_to_datetime(obj.get('timePublished'))


@content_version.field("scheduleArchiveEntity")
def resolve_time_archive_entity(obj, info):
    # pylint: disable=unused-argument
    return str_to_datetime(obj.get('scheduleArchiveEntity'))


@content_version.field("scheduleDeleteEntity")
def resolve_time_delete_entity(obj, info):
    # pylint: disable=unused-argument
    return str_to_datetime(obj.get('scheduleDeleteEntity'))


@content_version.field("group")
def resolve_group(obj, info):
    # pylint: disable=unused-argument
    if obj.get('groupGuid'):
        return Group.objects.get(id=obj.get('groupGuid'))


@content_version.field("owner")
def resolve_owner(obj, info):
    # pylint: disable=unused-argument
    if obj.get('ownerGuid'):
        return User.objects.get(id=obj.get('ownerGuid'))


@content_version.field("suggestedItems")
def resolve_suggested_items(obj, info):
    # pylint: disable=unused-argument
    if obj.get('suggestedItems'):
        return [load_entity_by_id(guid, ['core.Entity']) for guid in obj.get('suggestedItems')]


@content_version.field("parent")
def resolve_parent(obj, info):
    # pylint: disable=unused-argument
    if obj.get('containerGuid'):
        return load_entity_by_id(obj.get('containerGuid'), ['core.Entity'])
