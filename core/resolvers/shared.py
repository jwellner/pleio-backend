import html2text
from core.constances import ACCESS_TYPE
from core.models import EntityViewCount
from django.utils.text import Truncator
from django.core.exceptions import ObjectDoesNotExist

def resolve_entity_access_id(obj, info):
    # pylint: disable=unused-argument
    if obj.group and obj.group.subgroups:
        for subgroup in obj.group.subgroups.all():
            if ACCESS_TYPE.subgroup.format(subgroup.access_id) in obj.read_access:
                return subgroup.access_id
    if obj.group and ACCESS_TYPE.group.format(obj.group.id) in obj.read_access:
        return 4
    if ACCESS_TYPE.public in obj.read_access:
        return 2
    if ACCESS_TYPE.logged_in in obj.read_access:
        return 1
    return 0

def resolve_entity_write_access_id(obj, info):
    # pylint: disable=unused-argument
    if obj.group and obj.group.subgroups:
        for subgroup in obj.group.subgroups.all():
            if ACCESS_TYPE.subgroup.format(subgroup.access_id) in obj.write_access:
                return subgroup.access_id
    if obj.group and ACCESS_TYPE.group.format(obj.group.id) in obj.write_access:
        return 4
    if ACCESS_TYPE.public in obj.write_access:
        return 2
    if ACCESS_TYPE.logged_in in obj.write_access:
        return 1
    return 0

def resolve_entity_can_edit(obj, info):
    try:
        return obj.can_write(info.context["request"].user)
    except AttributeError:
        return False

def resolve_entity_featured(obj, info):
    # pylint: disable=unused-argument

    return {
        'image': obj.featured_image_url,
        'video': obj.featured_video,
        'positionY': obj.featured_position_y,
        'alt': obj.featured_alt
    }

def resolve_entity_guid(obj, info):
    # pylint: disable=unused-argument
    return obj.guid

def resolve_entity_status(obj, info):
    # pylint: disable=unused-argument
    return 200

def resolve_entity_title(obj, info):
    # pylint: disable=unused-argument
    return obj.title

def resolve_entity_description(obj, info):
    # pylint: disable=unused-argument
    return obj.description

def resolve_entity_rich_description(obj, info):
    # pylint: disable=unused-argument
    return obj.rich_description

def resolve_entity_excerpt(obj, info):
    # pylint: disable=unused-argument
    return Truncator(html2text.HTML2Text().handle(obj.description)).words(26)

def resolve_entity_tags(obj, info):
    # pylint: disable=unused-argument
    return obj.tags

def resolve_entity_time_created(obj, info):
    # pylint: disable=unused-argument
    return obj.created_at

def resolve_entity_time_updated(obj, info):
    # pylint: disable=unused-argument
    return obj.updated_at

def resolve_entity_can_vote(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.can_vote(info.context["request"].user)
    except AttributeError:
        return False

def resolve_entity_can_bookmark(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.can_bookmark(info.context["request"].user)
    except AttributeError:
        return False

def resolve_entity_has_voted(obj, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user
    try:
        return obj.has_voted(user)
    except AttributeError:
        return False

def resolve_entity_votes(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.vote_count()
    except AttributeError:
        return 0

def resolve_entity_is_bookmarked(obj, info):
    # pylint: disable=unused-argument
    user = info.context["request"].user
    try:
        return obj.is_bookmarked(user)
    except AttributeError:
        return False

def resolve_entity_can_comment(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.can_comment(info.context["request"].user)
    except AttributeError:
        return False

def resolve_entity_comments(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.comments.all()
    except AttributeError:
        return []

def resolve_entity_comment_count(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.comments.count()
    except AttributeError:
        return 0

def resolve_entity_is_following(obj, info):
    # pylint: disable=unused-argument
    try:
        return obj.is_following(info.context["request"].user)
    except AttributeError:
        return False

def resolve_entity_views(obj, info):
    # pylint: disable=unused-argument
    try:
        return EntityViewCount.objects.get(entity=obj).views
    except ObjectDoesNotExist:
        return 0

def resolve_entity_owner(obj, info):
    # pylint: disable=unused-argument
    return obj.owner
