from ariadne import ObjectType
from django.utils.text import slugify

news = ObjectType("News")


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
