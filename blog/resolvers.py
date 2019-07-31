from ariadne import ObjectType
from django.utils.text import slugify
from core.resolvers import resolve_entity_access_id, resolve_entity_can_edit, resolve_entity_write_access_id

blog = ObjectType("Blog")


@blog.field("excerpt")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return ""

@blog.field("hasVoted")
def resolve_has_voted(obj, info):
    # pylint: disable=unused-argument
    return False

@blog.field("commentCount")
def resolve_comment_count(obj, info):
    # pylint: disable=unused-argument
    return obj.comments.all().count()

@blog.field("comments")
def resolve_comments(obj, info):
    # pylint: disable=unused-argument
    return obj.comments.all()

@blog.field("isBookmarked")
def resolve_is_bookmarked(obj, info):
    # pylint: disable=unused-argument
    return False

@blog.field("canBookmark")
def resolve_can_bookmark(obj, info):
    # pylint: disable=unused-argument
    return True

@blog.field("featured")
def resolve_featured(obj, info):
    # pylint: disable=unused-argument
    return {
        'image': '',
        'video': '',
        'positionY': 0
    }

@blog.field("timeCreated")
def resolve_time_created(obj, info):
    # pylint: disable=unused-argument

    return obj.created_at


@blog.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument

    return '/blog/view/{}/{}'.format(
        obj.guid, slugify(obj.title)
    ).lower()


blog.set_field("canEdit", resolve_entity_can_edit)
blog.set_field("accessId", resolve_entity_access_id)
blog.set_field("writeAccessId", resolve_entity_write_access_id)

resolvers = [blog]
