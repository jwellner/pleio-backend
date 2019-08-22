from ariadne import ObjectType
from django.utils.text import slugify
from core.resolvers.shared import resolve_entity_access_id, resolve_entity_can_edit, resolve_entity_write_access_id, resolve_entity_featured

news = ObjectType("News")


@news.field("excerpt")
def resolve_excerpt(obj, info):
    # pylint: disable=unused-argument
    return ""

@news.field("hasVoted")
def resolve_has_voted(obj, info):
    # pylint: disable=unused-argument
    return False

@news.field("commentCount")
def resolve_comment_count(obj, info):
    # pylint: disable=unused-argument
    return 0

@news.field("isBookmarked")
def resolve_is_bookmarked(obj, info):
    # pylint: disable=unused-argument
    return False

@news.field("canBookmark")
def resolve_can_bookmark(obj, info):
    # pylint: disable=unused-argument
    return True


@news.field("timeCreated")
def resolve_time_created(obj, info):
    # pylint: disable=unused-argument

    return obj.created_at

@news.field("url")
def resolve_url(obj, info):
    # pylint: disable=unused-argument

    return '/news/view/{}/{}'.format(
        obj.guid, slugify(obj.title)
    ).lower()


news.set_field("canEdit", resolve_entity_can_edit)
news.set_field("accessId", resolve_entity_access_id)
news.set_field("writeAccessId", resolve_entity_write_access_id)
news.set_field("featured", resolve_entity_featured)

resolvers = [news]
