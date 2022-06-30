import json

from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import ugettext_lazy
from graphql import GraphQLError

from core.constances import (COULD_NOT_FIND, COULD_NOT_FIND_GROUP,
                             INVALID_DATE, USER_ROLES)
from core.lib import access_id_to_acl, clean_graphql_input, get_access_id
from core.models import Group
from core.resolvers import shared
from core.utils.entity import load_entity_by_id
from core.utils.tiptap_parser import Tiptap
from event.resolvers.mutation_attend_event import (
    resolve_attend_event, resolve_attend_event_without_account)
from event.resolvers.mutation_confirm_attend_event_without_account import \
    resolve_confirm_attend_event_without_account
from event.resolvers.mutation_delete_event_attendees import \
    resolve_delete_event_attendees
from event.resolvers.mutation_edit_event_attendee import \
    resolve_edit_event_attendee
from event.resolvers.mutation_messages import resolve_send_message_to_event

from ..models import Event

mutation = ObjectType("Mutation")

mutation.set_field("attendEvent", resolve_attend_event)
mutation.set_field("attendEventWithoutAccount", resolve_attend_event_without_account)
mutation.set_field("confirmAttendEventWithoutAccount", resolve_confirm_attend_event_without_account)
mutation.set_field("editEventAttendee", resolve_edit_event_attendee)
mutation.set_field("deleteEventAttendees", resolve_delete_event_attendees)
mutation.set_field("sendMessageToEvent", resolve_send_message_to_event)


def resolve_add_event(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

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

    shared.assert_group_member(user, group)

    entity = Event()

    entity.owner = user
    entity.group = group
    entity.parent = parent

    shared.resolve_add_access_id(entity, clean_input)
    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)
    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    shared.resolve_update_is_featured(entity, user, clean_input)

    resolve_validate_date(clean_input)
    resolve_update_startenddate(entity, clean_input)
    resolve_update_source(entity, clean_input)   
    resolve_update_location(entity, clean_input)
    resolve_update_max_attendees(entity, clean_input)
    resolve_update_ticket_link(entity, clean_input)
    resolve_update_rsvp(entity, clean_input)
    resolve_update_attend_without_account(entity, clean_input)
    resolve_update_qr_access(entity, clean_input)

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
    entity = load_entity_by_id(input['guid'], [Event])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    shared.resolve_update_title(entity, clean_input)

    shared.resolve_update_rich_description(entity, clean_input)

    shared.resolve_update_abstract(entity, clean_input)

    if 'containerGuid' in clean_input:
        try:
            container = Event.objects.get(id=clean_input.get("containerGuid"))
            if isinstance(container.parent, Event):
                raise GraphQLError("SUBEVENT_OF_SUBEVENT")
        except ObjectDoesNotExist:
            GraphQLError(COULD_NOT_FIND)

        entity.parent = container
        entity.group = container.group

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_access_id(entity, clean_input)

    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    shared.resolve_update_is_featured(entity, user, clean_input)

    resolve_validate_date(clean_input)
    resolve_update_startenddate(entity, clean_input)
    resolve_update_source(entity, clean_input)    
    resolve_update_location(entity, clean_input)
    resolve_update_ticket_link(entity, clean_input)
    resolve_update_max_attendees(entity, clean_input)
    resolve_update_rsvp(entity, clean_input)
    resolve_update_attend_without_account(entity, clean_input)
    resolve_update_qr_access(entity, clean_input)

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        shared.resolve_update_group(entity, clean_input)

        shared.resolve_update_owner(entity, clean_input)

        shared.resolve_update_time_created(entity, clean_input)

    entity.save()

    return {
        "entity": entity
    }


def copy_event(event_id, user, parent=None):
    # pylint: disable=redefined-builtin

    entity = Event.objects.get(id=event_id)

    now = timezone.now()

    attachments = entity.attachments_in_text()
    for x in attachments:
        attachment_copy = x.make_copy(user)
        original = "/attachment/%s" % x.id
        replacement = "/attachment/%s" % attachment_copy.id
        tiptap = Tiptap(entity.rich_description)
        tiptap.replace_url(original, replacement)
        tiptap.replace_src(original, replacement)
        entity.rich_description = json.dumps(tiptap.tiptap_json)

    if entity.featured_image:
        featured = entity.featured_image
        entity.featured_image = featured.make_copy(user)

    # preserve time of original event
    if entity.start_date:
        if entity.end_date:
            difference = entity.end_date - entity.start_date
        entity.start_date = entity.start_date.replace(
            year=now.year,
            month=now.month,
            day=now.day,
        )
        if entity.end_date:
            entity.end_date = entity.start_date + difference

    entity.owner = user
    entity.is_featured = False
    entity.is_pinned = False
    entity.notifications_created = False
    entity.published = None
    entity.created_at = now
    entity.updated_at = now
    entity.last_action = now
    entity.read_access = access_id_to_acl(entity, get_access_id(entity.read_access))
    entity.write_access = access_id_to_acl(entity, 0)

    if parent:
        entity.parent = parent

    # subevents keep original title
    if not parent:
        entity.title = ugettext_lazy("Copy %s") % entity.title

    entity.pk = None
    entity.id = None
    entity.save()

    return entity


def resolve_copy_event(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    event = load_entity_by_id(input['guid'], [Event])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(event, user)

    entity = copy_event(clean_input.get("guid"), user)

    resolve_copy_subevents(entity, event, user, clean_input)

    return {
        "entity": entity
    }

# Content property resolvers:

def resolve_validate_date(clean_input):
    if not clean_input.get("startDate", None) or not clean_input.get("endDate", None):
        raise GraphQLError(INVALID_DATE)

def resolve_update_startenddate(entity, clean_input):
    if 'startDate' in clean_input:
        entity.start_date = clean_input.get("startDate")
    if 'endDate' in clean_input:
        entity.end_date = clean_input.get("endDate")
    if entity.start_date > entity.end_date:
        raise GraphQLError(INVALID_DATE)

def resolve_update_location(entity, clean_input):
    if 'location' in clean_input:
        entity.location = clean_input.get("location")
    if 'locationLink' in clean_input:
        entity.location_link = clean_input.get("locationLink")
    if 'locationAddress' in clean_input:
        entity.location_address = clean_input.get("locationAddress")

def resolve_update_source(entity, clean_input):
    if 'source' in clean_input:
        entity.external_link = clean_input.get("source")

def resolve_update_ticket_link(entity, clean_input):
    if 'ticketLink' in clean_input:
        entity.ticket_link = clean_input['ticketLink']

def resolve_update_max_attendees(entity, clean_input):
    if 'maxAttendees' in clean_input:
        if clean_input.get("maxAttendees") == "":
            entity.max_attendees = None
        else:
            entity.max_attendees = int(clean_input.get("maxAttendees"))
        entity.process_waitinglist()

def resolve_update_rsvp(entity, clean_input):
    if 'rsvp' in clean_input:
        entity.rsvp = clean_input.get("rsvp")

def resolve_update_attend_without_account(entity, clean_input):
    if 'attendEventWithoutAccount' in clean_input:
        entity.attend_event_without_account = clean_input.get("attendEventWithoutAccount")

def resolve_update_qr_access(entity, clean_input):
    if 'qrAccess' in clean_input:
        entity.qr_access = clean_input.get("qrAccess")

def resolve_copy_subevents(entity, event, user, clean_input):
    if clean_input.get("copySubevents", True) and event.has_children():
        for child in event.children.all():
            copy_event(child.guid, user, entity)
