from graphql import GraphQLError

from core.constances import INVALID_DATE, COULD_NOT_ADD, SUBEVENT_OPERATION, NON_SUBEVENT_OPERATION
from core.lib import NumberIncrement


def resolve_assert_valid_date(clean_input):
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


def resolve_update_slot(entity, clean_input):
    if 'slot' in clean_input:
        # only allowed for sub-events.
        if not entity.parent:
            raise GraphQLError(SUBEVENT_OPERATION)

        value = clean_input['slot']
        if value.get('id', None):
            entity.slot = entity.parent.slots_available.get(pk=value.get('id', None))
        else:
            entity.slot = None



def resolve_update_slots_available(entity, clean_input):
    if 'slotsAvailable' in clean_input:
        # not allowed for sub-events
        if entity.parent:
            raise GraphQLError(NON_SUBEVENT_OPERATION)

        if not entity.id:
            raise GraphQLError(COULD_NOT_ADD)

        increment = NumberIncrement()
        for value in clean_input['slotsAvailable']:
            slot = entity.slots_available.filter(pk=value.get('id')).first()

            if value.get('delete', False):
                if slot:
                    slot.delete()
                continue

            if value.get('name', ''):
                if not slot:
                    slot = entity.slots_available.create(name=value.get('name'))
                else:
                    slot.name = value.get('name')

            slot.index = increment.next()
            slot.save()
