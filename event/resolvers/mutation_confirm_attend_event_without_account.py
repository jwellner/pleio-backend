from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from core.constances import (COULD_NOT_FIND, COULD_NOT_SAVE,
                             EMAIL_ALREADY_USED, INVALID_EMAIL,
                             EVENT_INVALID_STATE, EVENT_IS_FULL)
from core.lib import clean_graphql_input
from event.mail_builders.attend_event_confirm import submit_attend_event_wa_confirm
from event.mail_builders.qr_code import submit_mail_event_qr
from event.models import Event, EventAttendeeRequest, EventAttendee


def resolve_confirm_attend_event_without_account(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    clean_input = clean_graphql_input(input)

    email = clean_input.get("email")
    delete = clean_input.get("delete")
    # TODO: set default value for backwards compatibility, remove if frontend is altered
    state = clean_input.get("state", "accept")

    if state not in ["accept", "reject", "maybe", "waitinglist"]:
        raise GraphQLError(EVENT_INVALID_STATE)

    try:
        event = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        validate_email(email)
    except ValidationError:
        raise GraphQLError(INVALID_EMAIL)

    try:
        attendee_request = EventAttendeeRequest.objects.get(email=email, code=clean_input.get("code"), event=event)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not event.attend_event_without_account:
        raise GraphQLError(COULD_NOT_SAVE)

    # delete attendee and attendee request
    if delete:
        try:
            EventAttendee.objects.get(event=event, email=email).delete()
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)
        attendee_request.delete()

    # create attendee
    else:
        # check if already registered as attendee
        if EventAttendee.objects.filter(email=attendee_request.email, event=event):
            raise GraphQLError(EMAIL_ALREADY_USED)

        try:
            attendee = event.attendees.get(email=email)
        except ObjectDoesNotExist:
            attendee = None

        if not attendee:
            attendee = EventAttendee.objects.create(
                event=event,
                name=attendee_request.name,
                email=email,
            )

        if state == "accept":
            if event.is_full():
                raise GraphQLError(EVENT_IS_FULL)

        attendee.update_state(state)
        attendee.save()

        submit_attend_event_wa_confirm(attendee.id, attendee_request.code)

        if event.qr_access and state == "accept":
            submit_mail_event_qr(attendee)

        if state != "accept":
            event.process_waitinglist()

    return {
        "entity": event
    }
