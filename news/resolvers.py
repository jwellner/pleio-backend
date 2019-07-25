from ariadne import ObjectType
from django.utils.text import slugify

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


@news.field("featured")
def resolve_featured(obj, info):
    # pylint: disable=unused-argument
    return {
        'image': '',
        'video': '',
        'positionY': 0
    }


@news.field("canEdit")
def resolve_can_edit(obj, info):
    user = info.context.user

    return obj.can_write(user)


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


@news.field("accessId")
def resolve_access_id(obj, info):
    # pylint: disable=unused-argument

    return 1


resolvers = [news]
