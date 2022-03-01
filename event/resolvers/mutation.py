import json
from core.utils.tiptap_parser import Tiptap
from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, EVENT_IS_FULL, EVENT_INVALID_STATE, COULD_NOT_FIND_GROUP, INVALID_DATE, COULD_NOT_SAVE, USER_ROLES
from core.lib import get_access_id, remove_none_from_dict, access_id_to_acl, tenant_schema
from core.models import Group
from core.resolvers.shared import clean_abstract
from core.utils.convert import tiptap_to_text
from file.models import FileFolder
from file.tasks import resize_featured
from user.models import User
from django.utils.translation import ugettext_lazy
from django.utils import timezone

from ..models import Event, EventAttendee
from event.resolvers.mutation_attend_event_without_account import resolve_attend_event_without_account
from event.resolvers.mutation_confirm_attend_event_without_account import resolve_confirm_attend_event_without_account
from event.resolvers.mutation_delete_event_attendees import resolve_delete_event_attendees

mutation = ObjectType("Mutation")

mutation.set_field("attendEventWithoutAccount", resolve_attend_event_without_account)
mutation.set_field("confirmAttendEventWithoutAccount", resolve_confirm_attend_event_without_account)
mutation.set_field("deleteEventAttendees", resolve_delete_event_attendees)

@mutation.field("attendEvent")
def resolve_attend_event(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        event = Event.objects.visible(user).get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        attendee = event.attendees.get(user=user)
    except ObjectDoesNotExist:
        attendee = None

    if not attendee:
        attendee = EventAttendee()
        attendee.event = event
        attendee.user = user

    if clean_input.get("state") not in ["accept", "reject", "maybe", "waitinglist"]:
        raise GraphQLError(EVENT_INVALID_STATE)

    if clean_input.get("state") == "accept" and not attendee.state == "accept":
        if event.is_full():
            raise GraphQLError(EVENT_IS_FULL)

    attendee.state = clean_input.get("state")

    attendee.save()

    if clean_input.get("state") != "accept":
        event.process_waitinglist()

    return {
        "entity": event
    }

def resolve_add_event(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements


    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None
    parent = None

    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            try:
                parent = Event.objects.get(id=clean_input.get("containerGuid"))
                if isinstance(parent.parent, Event):
                    raise GraphQLError("SUBEVENT_OF_SUBEVENT")
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND_GROUP)

    if parent and parent.group:
        group = parent.group

    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError("NOT_GROUP_MEMBER")

    entity = Event()

    entity.owner = user
    entity.tags = clean_input.get("tags")

    entity.group = group
    entity.parent = parent

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.title = clean_input.get("title")
    entity.rich_description = clean_input.get("richDescription")
    entity.description = tiptap_to_text(entity.rich_description)
    if 'abstract' in clean_input:
        abstract = clean_input.get("abstract")
        clean_abstract(abstract)
        entity.abstract = abstract

    if 'featured' in clean_input:
        entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
        entity.featured_video = clean_input.get("featured").get("video", None)
        entity.featured_video_title = clean_input.get("featured").get("videoTitle", "")
        entity.featured_alt = clean_input.get("featured").get("alt", "")
        if entity.featured_video:
            entity.featured_image = None
        elif clean_input.get("featured").get("image"):

            imageFile = FileFolder.objects.create(
                owner=entity.owner,
                upload=clean_input.get("featured").get("image"),
                read_access=entity.read_access,
                write_access=entity.write_access
            )

            resize_featured.delay(tenant_schema(), imageFile.guid)

            entity.featured_image = imageFile
    else:
        entity.featured_image = None
        entity.featured_position_y = 0
        entity.featured_video = None
        entity.featured_video_title = ""
        entity.featured_alt = ""

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    if not clean_input.get("startDate", None) or not clean_input.get("endDate", None):
        raise GraphQLError(INVALID_DATE)

    entity.start_date = clean_input.get("startDate")
    entity.end_date = clean_input.get("endDate")

    if entity.start_date > entity.end_date:
        raise GraphQLError(INVALID_DATE)

    entity.external_link = clean_input.get("source", "")
    entity.location = clean_input.get("location", "")

    if 'maxAttendees' in clean_input:
        if clean_input.get("maxAttendees") == "":
            entity.max_attendees = None
        else:
            entity.max_attendees = int(clean_input.get("maxAttendees"))

    entity.rsvp = clean_input.get("rsvp", False)
    entity.attend_event_without_account = clean_input.get("attendEventWithoutAccount", False)

    if 'timePublished' in clean_input:
        entity.published = clean_input.get("timePublished", None)

    entity.save()

    entity.add_follow(user)

    return {
        "entity": entity
    }


def resolve_edit_event(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'title' in clean_input:
        entity.title = clean_input.get("title")

    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")
        entity.description = tiptap_to_text(entity.rich_description)

    if 'abstract' in clean_input:
        abstract = clean_input.get("abstract")
        clean_abstract(abstract)
        entity.abstract = abstract

    if 'containerGuid' in clean_input:
        try:
            container = Event.objects.get(id=clean_input.get("containerGuid"))
            if isinstance(container.parent, Event):
                raise GraphQLError("SUBEVENT_OF_SUBEVENT")
        except ObjectDoesNotExist:
            GraphQLError(COULD_NOT_FIND)

        entity.parent = container
        entity.group = container.group

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")
    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    if 'featured' in clean_input:
        entity.featured_position_y = clean_input.get("featured").get("positionY", 0)
        entity.featured_video = clean_input.get("featured").get("video", None)
        entity.featured_video_title = clean_input.get("featured").get("videoTitle", "")
        entity.featured_alt = clean_input.get("featured").get("alt", "")
        if entity.featured_video:
            entity.featured_image = None
        elif clean_input.get("featured").get("image"):

            if entity.featured_image:
                imageFile = entity.featured_image
                imageFile.resized_images.all().delete()
            else:
                imageFile = FileFolder()

            imageFile.owner = entity.owner
            imageFile.read_access = entity.read_access
            imageFile.write_access = entity.write_access
            imageFile.upload = clean_input.get("featured").get("image")
            imageFile.save()

            resize_featured.delay(tenant_schema(), imageFile.guid)

            entity.featured_image = imageFile
    else:
        entity.featured_image = None
        entity.featured_position_y = 0
        entity.featured_video = None
        entity.featured_video_title = ""
        entity.featured_alt = ""

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    if not clean_input.get("startDate", None) or not clean_input.get("endDate", None):
        raise GraphQLError(INVALID_DATE)

    if 'startDate' in clean_input:
        entity.start_date = clean_input.get("startDate")
    if 'endDate' in clean_input:
        entity.end_date = clean_input.get("endDate")

    if entity.start_date > entity.end_date:
        raise GraphQLError(INVALID_DATE)

    if 'source' in clean_input:
        entity.external_link = clean_input.get("source")
    if 'location' in clean_input:
        entity.location = clean_input.get("location")

    if 'maxAttendees' in clean_input:
        if clean_input.get("maxAttendees") == "":
            entity.max_attendees = None
        else:
            entity.max_attendees = int(clean_input.get("maxAttendees"))

    if 'rsvp' in clean_input:
        entity.rsvp = clean_input.get("rsvp")
    if 'attendEventWithoutAccount' in clean_input:
        entity.attend_event_without_account = clean_input.get("attendEventWithoutAccount")

    if 'timePublished' in clean_input:
        entity.published = clean_input.get("timePublished", None)

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        if 'groupGuid' in input:
            if input.get("groupGuid") is None:
                entity.group = None
            else:
                try:
                    group = Group.objects.get(id=clean_input.get("groupGuid"))
                    entity.group = group
                except ObjectDoesNotExist:
                    raise GraphQLError(COULD_NOT_FIND)

        if 'ownerGuid' in clean_input:
            try:
                owner = User.objects.get(id=clean_input.get("ownerGuid"))
                entity.owner = owner
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)

        if 'timeCreated' in clean_input:
            entity.created_at = clean_input.get("timeCreated")

    entity.save()

    return {
        "entity": entity
    }


def resolve_copy_event(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    attachments = entity.attachments_in_text()
    for x in attachments:
        attachment_copy = x.make_copy(user)
        original = "/attachment/%s" %x.id
        replacement = "/attachment/%s" %attachment_copy.id
        tiptap = Tiptap(entity.rich_description)
        tiptap.replace_url(original, replacement)
        tiptap.replace_src(original, replacement) 
        entity.rich_description = json.dumps(tiptap.tiptap_json)

    entity.title = ugettext_lazy("Copy %s") %entity.title
    entity.start_date = timezone.now()
    entity.end_date = None
    entity.owner = user
    entity.is_featured = False
    entity.is_pinned = False
    entity.notifications_created = False
    entity.published = None
    entity.created_at = timezone.now()
    entity.updated_at = timezone.now()
    entity.last_action = timezone.now()
    entity.read_access = access_id_to_acl(entity, get_access_id(entity))
    entity.write_access = access_id_to_acl(entity, 0)

    entity.pk = None
    entity.id = None
    entity.save()

    return {
        "entity": entity
    }
