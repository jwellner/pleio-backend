import logging
import os

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import gettext
from elasticsearch_dsl import Search
from graphql import GraphQLError
from online_planner.meetings_api import MeetingsApi

from cms.row_resolver import RowSerializer
from core import config
from core.constances import ACCESS_TYPE, USER_ROLES, FILE_NOT_CLEAN
from core import constances
from core.exceptions import AttachmentVirusScanError
from core.lib import (access_id_to_acl, html_to_text,
                      tenant_schema, get_access_id, strip_exif)
from core.models import EntityViewCount, Group, VideoCallGuest
from core.models.revision import Revision
from core.tasks.cleanup_tasks import cleanup_featured_image_files
from core.utils.convert import tiptap_to_text, truncate_rich_description
from core.utils.entity import load_entity_by_id
from file.models import FileFolder
from user.models import User

LOGGER = logging.getLogger(__name__)


def resolve_entity_access_id(obj, info):
    # pylint: disable=unused-argument
    # EM: HIER (2)
    return get_access_id(obj.read_access)


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
        'imageGuid': obj.featured_image_guid,
        'video': obj.featured_video,
        'videoTitle': obj.featured_video_title,
        'positionY': obj.featured_position_y,
        'alt': obj.featured_alt
    }


def resolve_entity_suggested_items(obj, info):
    # pylint: disable=unused-argument

    suggested = []
    if obj.suggested_items:
        for item in obj.suggested_items:
            entity = load_entity_by_id(item, ['blog.Blog', 'news.News'], fail_if_not_found=False)
            if entity:
                suggested.append(entity)

    return suggested


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


def resolve_entity_last_seen(obj, info):
    # pylint: disable=unused-argument
    return obj.last_seen


def _comment_count_from_index(obj):
    try:
        query = Search(index='_all') \
            .query('match', id=obj.guid) \
            .source(['id', 'comments'])
        for match in query.execute():
            if match.id == obj.guid:
                return len(match.comments)
    except Exception as e:
        LOGGER.error(e)
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


def resolve_entity_categories(obj, info):
    # pylint: disable=unused-argument
    return obj.category_tags


def resolve_add_suggested_items(entity, clean_input):
    clean_input.setdefault('suggestedItems', [])
    resolve_update_suggested_items(entity, clean_input)


def resolve_start_revision(entity, user):
    if entity.has_revisions():
        revision = Revision()
        revision.author = user
        revision.start_tracking_changes(entity)
        return revision


def store_update_revision(revision, container):
    if revision:
        revision.store_update_revision(container)


def store_initial_revision(container):
    if container.has_revisions():
        Revision().store_initial_version(container)


# Update
def resolve_update_suggested_items(entity, clean_input):
    if 'suggestedItems' in clean_input:
        entity.suggested_items = clean_input.get("suggestedItems")


def update_updated_at(entity):
    entity.updated_at = timezone.now()


def update_publication_dates(entity, clean_input):
    if 'timePublished' in clean_input:
        entity.published = clean_input.get("timePublished")
        entity.update_last_action(entity.published)

    if 'scheduleArchiveEntity' in clean_input:
        entity.schedule_archive_after = clean_input.get("scheduleArchiveEntity") or None
        if entity.schedule_archive_after and entity.schedule_archive_after <= timezone.now():
            entity.is_archived = True

    if 'scheduleDeleteEntity' in clean_input:
        entity.schedule_delete_after = clean_input.get("scheduleDeleteEntity") or None

    if entity.schedule_delete_after and entity.schedule_archive_after:
        if entity.schedule_delete_after < entity.schedule_archive_after:
            raise GraphQLError(constances.INVALID_ARCHIVE_AFTER_DATE)


def update_featured_image(entity, clean_input, image_owner=None):
    if 'featured' not in clean_input:
        return

    featured = clean_input["featured"]
    if featured.get("video", ""):
        featured['imageGuid'] = None
    elif featured.get("image"):
        featured_image = FileFolder.objects.create(
            owner=entity.owner,
            upload=featured.get("image"),
        )
        if hasattr(entity, 'read_access'):
            featured_image.read_access = entity.read_access
            featured_image.write_access = entity.write_access
        else:
            featured_image.read_access = [ACCESS_TYPE.public]
            featured_image.write_access = [ACCESS_TYPE.user.format(image_owner.id)]
        featured_image.save()

        featured['imageGuid'] = featured_image.guid
        featured.pop('image', None)

        if featured_image.scan():
            from file.tasks import resize_featured
            resize_featured.delay(tenant_schema(), featured_image.guid)
        else:
            featured_image.delete()
            raise GraphQLError(constances.FILE_NOT_CLEAN.format(os.path.basename(featured_image.upload.name)))
        post_upload_file(featured_image)

    elif not featured.get("imageGuid"):
        # No image, no guid, no video: cleanup.
        featured['imageGuid'] = None
        featured['positionY'] = 0
        featured['video'] = None
        featured['videoTitle'] = ""
        featured['alt'] = ""

    original = entity.serialize_featured()
    entity.unserialize_featured(featured)

    if not hasattr(entity, 'has_revisions') or not entity.has_revisions():
        if entity.is_featured_image_changed(original):
            cleanup_featured_image_files(original['image'])


def resolve_update_title(entity, clean_input):
    if 'title' in clean_input:
        title = clean_input.get("title").strip()
        assert_valid_title(title)
        entity.title = title


def resolve_update_rich_description(entity, clean_input):
    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")


def resolve_update_introduction(entity, clean_input):
    if 'introduction' in clean_input:
        entity.introduction = clean_input.get("introduction")


def resolve_update_tags(entity, clean_input):
    if 'tags' in clean_input:
        entity.tags = clean_input["tags"]

    if 'tagCategories' in clean_input:
        entity.category_tags = clean_input['tagCategories']


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
                raise GraphQLError(constances.COULD_NOT_FIND)
        else:
            entity.group = None


def resolve_update_owner(entity, clean_input):
    if 'ownerGuid' in clean_input:
        try:
            currentOwnerGuid = entity.owner.guid if entity.owner else None
            if clean_input['ownerGuid'] != currentOwnerGuid:
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
            raise GraphQLError(constances.COULD_NOT_FIND)


def resolve_update_time_created(entity, clean_input):
    if 'timeCreated' in clean_input:
        entity.created_at = clean_input["timeCreated"]


def resolve_update_abstract(entity, clean_input):
    if 'abstract' in clean_input:
        abstract = clean_input.get("abstract")
        assert_valid_abstract(abstract)
        entity.abstract = abstract


def update_is_featured(entity, user, clean_input):
    if 'isFeatured' in clean_input and (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
        entity.is_featured = clean_input.get("isFeatured")


def update_is_recommended(entity, user, clean_input):
    if 'isRecommended' in clean_input and (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
        entity.is_recommended = clean_input.get("isRecommended")


# Group
def get_group(clean_input):
    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
            return group
        except ObjectDoesNotExist:
            raise GraphQLError(constances.COULD_NOT_FIND_GROUP)
    else:
        return None


# Checks
def assert_administrator(user):
    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(constances.USER_NOT_SITE_ADMIN)


def assert_authenticated(user):
    if not user.is_authenticated:
        raise GraphQLError(constances.NOT_LOGGED_IN)


def assert_superadmin(user):
    if not user.is_superadmin:
        raise GraphQLError(constances.USER_NOT_SUPERADMIN)


def assert_is_profile_set_manager(user, profileSetGuid):
    if not user.profile_sets.filter(pk=profileSetGuid).exists():
        raise GraphQLError(constances.NOT_AUTHORIZED)


def load_user(guid):
    try:
        return User.objects.get(id=guid)
    except User.DoesNotExist:
        raise GraphQLError(constances.COULD_NOT_FIND_USER)


def assert_write_access(entity, user):
    if not entity.can_write(user):
        raise GraphQLError(constances.COULD_NOT_SAVE)


def assert_group_member(user, group):
    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(constances.USER_NOT_MEMBER_OF_GROUP)


def assert_valid_title(title):
    if len(title) == 0 or len(title) > 256:
        raise GraphQLError(constances.INVALID_VALUE)


def assert_valid_abstract(abstract):
    text = html_to_text(abstract).strip()
    if len(text) > config.MAX_CHARACTERS_IN_ABSTRACT:
        raise GraphQLError(constances.TEXT_TOO_LONG)


def assert_isnt_me(left_user, right_user):
    if left_user == right_user:
        raise GraphQLError(constances.COULD_NOT_SAVE)


def has_full_admin_abilities_on_user(obj, info):
    try:
        operating_user = info.context["request"].user
        assert_authenticated(operating_user)
        assert_isnt_me(obj, operating_user)

        if obj.is_superadmin:
            return operating_user.is_superadmin

        assert_administrator(operating_user)
        return True
    except GraphQLError:
        return False


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


def resolve_update_rows(entity, clean_input, user):
    try:
        if 'rows' in clean_input:
            entity.row_repository = []
            for row in clean_input['rows']:
                rowSerializer = RowSerializer(row, acting_user=user)
                entity.row_repository.append(rowSerializer.serialize())
    except AttachmentVirusScanError as e:
        raise GraphQLError(constances.FILE_NOT_CLEAN.format(str(e)))


def post_upload_file(entity: FileFolder):
    if not config.PRESERVE_FILE_EXIF and entity.is_image():
        strip_exif(entity.upload)


def scan_file(file, delete_if_virus=False, delete_from_disk=False):
    if file.is_file() and not file.scan():
        filename = file.title
        if delete_from_disk:
            os.unlink(file.upload.path)
        if delete_if_virus:
            file.delete()
        raise GraphQLError(FILE_NOT_CLEAN.format(filename))


def assert_meetings_enabled():
    if not config.ONLINEAFSPRAKEN_ENABLED:
        raise GraphQLError(constances.MEETINGS_NOT_ENABLED)


def assert_videocall_enabled():
    if not config.VIDEOCALL_ENABLED:
        raise GraphQLError(constances.VIDEOCALL_NOT_ENABLED)


def assert_videocall_profilepage():
    if not config.VIDEOCALL_PROFILEPAGE:
        raise GraphQLError(constances.VIDEOCALL_PROFILEPAGE_NOT_AVAILABLE)


def assert_videocall_limit():
    last_hour = VideoCallGuest.objects.filter(created_at__gte=timezone.localtime() - timezone.timedelta(hours=1)).count()
    if last_hour >= config.VIDEOCALL_THROTTLE:
        raise GraphQLError(constances.VIDEOCALL_LIMIT_REACHED)


def resolve_load_appointment_types():
    appointement_types = MeetingsApi().get_appointment_types()
    has_videocall = {s['id']: s['hasVideocall'] for s in config.VIDEOCALL_APPOINTMENT_TYPE}
    return [{
        "id": t['Id'],
        'name': t['Name'] or gettext('Appointment'),
        'hasVideocall': has_videocall.get(t['Id']) or False} for t in appointement_types]


def resolve_load_agendas():
    agendas = MeetingsApi().get_agendas()
    return [{'id': a['Id'], 'name': a['Name'] or gettext('Agenda')} for a in agendas]
