from django.core.exceptions import ObjectDoesNotExist
from elasticsearch_dsl import Search
from graphql import GraphQLError

from blog.models import Blog
from core import config
from core.constances import (ACCESS_TYPE, COULD_NOT_FIND, COULD_NOT_FIND_GROUP,
                             COULD_NOT_SAVE, INVALID_ARCHIVE_AFTER_DATE,
                             NOT_LOGGED_IN, TEXT_TOO_LONG,
                             USER_NOT_MEMBER_OF_GROUP, USER_NOT_SITE_ADMIN,
                             USER_ROLES)
from core.lib import (access_id_to_acl, entity_access_id, html_to_text,
                      tenant_schema)
from core.models import EntityViewCount, Group
from core.models.revision import Revision
from core.utils.convert import tiptap_to_text, truncate_rich_description
from core.utils.entity import load_entity_by_id
from file.models import FileFolder
from file.tasks import resize_featured
from news.models import News
from user.models import User


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


def resolve_entity_related_items(obj, info):
    # pylint: disable=unused-argument
    related = []
    if obj.related_items:
        for item in obj.related_items:
            entity = load_entity_by_id(item, [Blog, News], fail_if_not_found=False)
            if entity:
                related.append(entity)

    total = len(related)
    return {
        'total': total,
        'edges': related
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


def resolve_entity_schedule_archive_entity(obj, _):
    return obj.schedule_archive_after


def resolve_entity_schedule_delete_entity(obj, _):
    return obj.schedule_delete_after


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


def assert_valid_abstract(abstract):
    text = html_to_text(abstract).strip()
    if len(text) > config.MAX_CHARACTERS_IN_ABSTRACT:
        raise GraphQLError(TEXT_TOO_LONG)


def resolve_add_related_items(entity, clean_input):
    clean_input.setdefault('relatedItems', [])
    resolve_update_related_items(entity, clean_input)


def resolve_entity_revision(obj, info):
    # pylint: disable=unused-argument
    return obj.last_revision


def resolve_start_revision(entity):
    if not entity.last_revision:
        revision = Revision()
        revision.object = entity
        entity.last_revision = revision


def resolve_store_revision(entity):
    revision = entity.last_revision
    revision.save()


def resolve_apply_revision(entity, revision):
    if revision:
        entity.rich_description = revision.content.get("richDescription")
        entity.last_revision = None


# Update
def resolve_update_related_items(entity, clean_input):
    if 'relatedItems' in clean_input:
        entity.related_items = clean_input.get("relatedItems")


def update_publication_dates(entity, clean_input):
    if 'timePublished' in clean_input:
        entity.published = clean_input.get("timePublished")

    if 'scheduleArchiveEntity' in clean_input:
        entity.schedule_archive_after = clean_input.get("scheduleArchiveEntity") or None

    if 'scheduleDeleteEntity' in clean_input:
        entity.schedule_delete_after = clean_input.get("scheduleDeleteEntity") or None

    if entity.schedule_delete_after and entity.schedule_archive_after:
        if entity.schedule_delete_after < entity.schedule_archive_after:
            raise GraphQLError(INVALID_ARCHIVE_AFTER_DATE)


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


def resolve_update_title(entity, clean_input):
    if 'title' in clean_input:
        entity.title = clean_input.get("title")


def resolve_update_rich_description(entity, clean_input, revision=False):
    if 'richDescription' in clean_input:
        if revision:
            active_revision = entity.last_revision
            if active_revision.content:
                active_revision.content["richDescription"] = clean_input.get("richDescription")
            else:
                active_revision.content = {"richDescription": clean_input.get("richDescription")}
        else:
            entity.rich_description = clean_input.get("richDescription")


def resolve_update_tags(entity, clean_input):
    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")


def resolve_add_access_id(entity, clean_input):
    clean_input.setdefault('accessId', 0)
    clean_input.setdefault('writeAccessId', 0)
    resolve_update_access_id(entity, clean_input)


def resolve_update_access_id(entity, clean_input):
    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))


def resolve_update_group(entity, clean_input):
    if 'groupGuid' in clean_input:
        if clean_input["groupGuid"]:
            try:
                entity.group = Group.objects.get(id=clean_input["groupGuid"])
            except Group.DoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)
        else:
            entity.group = None


def resolve_update_owner(entity, clean_input):
    if 'ownerGuid' in clean_input:
        try:
            previous_owner_formatted = ACCESS_TYPE.user.format(entity.owner.id)
            owner = User.objects.get(id=clean_input.get("ownerGuid"))
            entity.owner = owner
            owner_formatted = ACCESS_TYPE.user.format(owner.id)
            if previous_owner_formatted in entity.read_access:
                entity.read_access = [i for i in entity.read_access if i != previous_owner_formatted]
                entity.read_access.append(owner_formatted)
            if previous_owner_formatted in entity.write_access:
                entity.write_access = [i for i in entity.write_access if i != previous_owner_formatted]
                entity.write_access.append(owner_formatted)
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)


def resolve_update_time_created(entity, clean_input):
    if 'timeCreated' in clean_input:
        entity.created_at = clean_input.get("timeCreated")


def resolve_update_abstract(entity, clean_input):
    if 'abstract' in clean_input:
        abstract = clean_input.get("abstract")
        assert_valid_abstract(abstract)
        entity.abstract = abstract


def resolve_update_is_featured(entity, user, clean_input):
    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")


def resolve_update_is_recommended(entity, user, clean_input):
    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isRecommended' in clean_input:
            entity.is_recommended = clean_input.get("isRecommended")


# Group
def get_group(clean_input):
    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
            return group
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)
    else:
        return None


# Checks
def assert_administrator(user):
    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)


def assert_authenticated(user):
    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)


def assert_write_access(entity, user):
    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)


def assert_group_member(user, group):
    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)


# Site setting profile field

def resolve_update_is_editable(profile_field, clean_input):
    if 'isEditable' in clean_input:
        profile_field.is_editable_by_user = clean_input["isEditable"]


def resolve_update_is_filter(profile_field, clean_input):
    if 'isFilter' in clean_input:
        profile_field.is_filter = clean_input["isFilter"]


def resolve_update_is_in_overview(profile_field, clean_input):
    if 'isInOverview' in clean_input:
        profile_field.is_in_overview = clean_input["isInOverview"]


def resolve_update_is_on_v_card(profile_field, clean_input):
    if 'isOnVcard' in clean_input:
        profile_field.is_on_vcard = clean_input['isOnVcard']


def resolve_update_is_in_onboarding(profile_field, clean_input):
    if 'isInOnboarding' in clean_input:
        profile_field.is_in_onboarding = clean_input["isInOnboarding"]


def resolve_update_is_mandatory(profile_field, clean_input):
    if 'isMandatory' in clean_input:
        profile_field.is_mandatory = clean_input["isMandatory"]
