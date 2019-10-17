from ariadne import ObjectType
from django.utils.text import slugify
from core.resolvers import shared


task = ObjectType("Task")


@task.field("subtype")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return obj.type_to_string()

@task.field("inGroup")
def resolve_in_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group is not None

@task.field("group")
def resolve_group(obj, info):
    # pylint: disable=unused-argument
    return obj.group

@task.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument

    prefix = ''

    if obj.group:
        prefix = '/groups/view/{}/{}'.format(
            obj.group.guid, slugify(obj.group.name)
        )

    return '{}/task/view/{}/{}'.format(
        prefix, obj.guid, slugify(obj.title)
    ).lower()

@task.field("state")
def resolve_state(obj, info):
    # pylint: disable=unused-argument
    return obj.state

@task.field("canComment")
def resolve_can_comment(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not by tasks"""
    return False

@task.field("canVote")
def resolve_can_vote(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not by tasks"""
    return False

@task.field("isFollowing")
def resolve_is_following(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not by tasks"""
    return False

@task.field("commentCount")
def resolve_comment_count(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not by tasks"""
    return 0

@task.field("comments")
def resolve_comments(obj, info):
    # pylint: disable=unused-argument
    """Deprecated: not by tasks"""
    return []


task.set_field("guid", shared.resolve_entity_guid)
task.set_field("status", shared.resolve_entity_status)
task.set_field("title", shared.resolve_entity_title)
task.set_field("description", shared.resolve_entity_description)
task.set_field("richDescription", shared.resolve_entity_rich_description)
task.set_field("excerpt", shared.resolve_entity_excerpt)
task.set_field("tags", shared.resolve_entity_tags)
task.set_field("timeCreated", shared.resolve_entity_time_created)
task.set_field("timeUpdated", shared.resolve_entity_time_updated)
task.set_field("canEdit", shared.resolve_entity_can_edit)
task.set_field("accessId", shared.resolve_entity_access_id)
task.set_field("writeAccessId", shared.resolve_entity_write_access_id)
task.set_field("views", shared.resolve_entity_views)
task.set_field("owner", shared.resolve_entity_owner)
