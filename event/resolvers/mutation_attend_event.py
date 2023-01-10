from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from graphql import GraphQLError

from core import config
from core.constances import (COULD_NOT_FIND, EMAIL_ALREADY_USED,
                             EVENT_INVALID_STATE, EVENT_IS_FULL, INVALID_EMAIL,
                             NOT_LOGGED_IN)
from core.lib import clean_graphql_input, generate_code, get_full_url
from event.lib import validate_name
from event.mail_builders.attend_event_request import \
    submit_attend_event_wa_request
from event.mail_builders.qr_code import submit_mail_event_qr
from event.models import Event, EventAttendee, EventAttendeeRequest
from event.resolvers import shared as event_shared


def resolve_attend_event_without_account(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument

    clean_input = clean_graphql_input(input, ['resend'])
    email = clean_input.get("email")
    name = validate_name(clean_input.get("name"))

    try:
        event = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        validate_email(email)
    except ValidationError:
        raise GraphQLError(INVALID_EMAIL)

    code = ""
    try:
        code = EventAttendeeRequest.objects.get(email=email, event=event).code
    except ObjectDoesNotExist:
        pass

    if code and clean_input.get("resend") is not True:
        raise GraphQLError(EMAIL_ALREADY_USED)

    if not code:
        code = generate_code()
        EventAttendeeRequest.objects.create(code=code, email=email, event=event, name=name)

    submit_attend_event_wa_request({
        'event': event.guid,
        'email': email,
        'language': config.LANGUAGE,
        'link': get_full_url(f"/events/confirm/{event.guid}?email={email}&code={code}"),
    })

    return {
        "entity": event
    }


def resolve_attend_event(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

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

    if not clean_input.get("state"):
        if attendee:
            event_shared.resolve_delete_attendee(attendee)
        return {
            "entity": event
        }

    if not attendee:
        attendee = EventAttendee()
        attendee.event = event
        attendee.user = user
        attendee.email = user.email
        attendee.name = user.name

    if clean_input["state"] not in ["accept", "reject", "maybe", "waitinglist"]:
        raise GraphQLError(EVENT_INVALID_STATE)

    if clean_input["state"] == "accept" and not attendee.state == "accept":
        if event.is_full():
            raise GraphQLError(EVENT_IS_FULL)

    attendee.update_state(clean_input["state"])
    attendee.updated_at = timezone.now()
    attendee.save()

    if clean_input.get("state") != "accept":
        event.process_waitinglist()

    if event.qr_access and clean_input.get("state") == "accept":
        submit_mail_event_qr(attendee)

    return {
        "entity": event
    }
