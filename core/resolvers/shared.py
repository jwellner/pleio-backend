from elasticsearch_dsl import Search

from core.constances import ACCESS_TYPE, TEXT_TOO_LONG
from core.models import EntityViewCount
from django.core.exceptions import ObjectDoesNotExist

from core.utils.convert import tiptap_to_text, truncate_rich_description
from graphql import GraphQLError
from core.lib import html_to_text, tenant_schema, entity_access_id
from file.models import FileFolder
from file.tasks import resize_featured


def resolve_entity_access_id(obj, info):
    # pylint: disable=unused-argument
    return entity_access_id(obj)


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
        'videoTitle': obj.featured_video_title,
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


def resolve_entity_abstract(obj, info):
    # pylint: disable=unused-argument
    return obj.abstract


def resolve_entity_description(obj, info):
    # pylint: disable=unused-argument
    return tiptap_to_text(obj.rich_description)


def resolve_entity_rich_description(obj, info):
    # pylint: disable=unused-argument
    return obj.rich_description


def resolve_entity_excerpt(obj, info):
    # pylint: disable=unused-argument
    if hasattr(obj, 'excerpt'):
        return obj.excerpt

    return truncate_rich_description(obj.rich_description)


def resolve_entity_tags(obj, info):
    # pylint: disable=unused-argument
    return obj.tags


def resolve_entity_time_created(obj, info):
    # pylint: disable=unused-argument
    return obj.created_at


def resolve_entity_time_updated(obj, info):
    # pylint: disable=unused-argument
    return obj.updated_at


def resolve_entity_time_published(obj, info):
    # pylint: disable=unused-argument
    return obj.published


def resolve_entity_status_published(obj, info):
    # pylint: disable=unused-argument
    return obj.status_published


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
    count = _comment_count_from_index(obj)
    if count is None:
        return _comment_count_from_object(obj)
    return count


def _comment_count_from_index(obj):
    query = Search(index='_all') \
        .query('match', id=obj.guid) \
        .source(['id', 'comments'])
    for match in query.execute():
        if match.id == obj.guid:
            return len(match.comments)
    return None


def _comment_count_from_object(obj):
    try:
        return len([c.id for c in obj.get_flat_comment_list()])
    except AttributeError:
        pass
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


def resolve_entity_is_pinned(obj, info):
    # pylint: disable=unused-argument
    if hasattr(obj, "is_pinned"):
        return obj.is_pinned
    return False


def update_featured_image(entity, clean_input, image_owner=None):
    # pylint: disable=import-outside-toplevel
    from core.tasks.cleanup_tasks import cleanup_featured_image_files

    if 'featured' in clean_input:
        entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
        entity.featured_video = clean_input.get("featured").get("video", "")
        entity.featured_video_title = clean_input.get("featured").get("videoTitle", "")
        entity.featured_alt = clean_input.get("featured").get("alt", "")
        if entity.featured_video:
            cleanup_featured_image_files(entity.featured_image)
            entity.featured_image = None
        elif clean_input.get("featured").get("image"):
            cleanup_featured_image_files(entity.featured_image)

            entity.featured_image = FileFolder.objects.create(
                owner=entity.owner,
                upload=clean_input.get("featured").get("image")
            )
            if hasattr(entity, 'read_access'):
                entity.featured_image.read_access = entity.read_access
                entity.featured_image.write_access = entity.write_access
            else:
                entity.featured_image.read_access = [ACCESS_TYPE.public]
                entity.featured_image.write_access = [ACCESS_TYPE.user.format(image_owner.id)]
            entity.featured_image.save()

            resize_featured.delay(tenant_schema(), entity.featured_image.id)
        else:
            # nothing changed.
            pass
    else:
        cleanup_featured_image_files(entity.featured_image)

        entity.featured_image = None
        entity.featured_position_y = 0
        entity.featured_video = None
        entity.featured_video_title = ""
        entity.featured_alt = ""


# TODO: this function should be moved later on to a shared class
def clean_abstract(abstract):
    text = html_to_text(abstract).strip()
    if len(text) > 320:
        raise GraphQLError(TEXT_TOO_LONG)
