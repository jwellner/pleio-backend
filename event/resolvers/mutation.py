from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from ariadne import ObjectType
from event.models import Event, EventAttendee
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, EVENT_IS_FULL, EVENT_INVALID_STATE
from core.lib import remove_none_from_dict


mutation = ObjectType("Mutation")

@mutation.field("attendEvent")
def resolve_attend_event(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
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

    if clean_input.get("state") not in ["accept", "reject", "maybe"]:
        raise GraphQLError(EVENT_INVALID_STATE)

    if clean_input.get("state") == "accept" and not attendee.state == "accept":
        if event.max_attendees and event.attendees.filter(state="accept").count() >= event.max_attendees:
            raise GraphQLError(EVENT_IS_FULL)

    attendee.state = clean_input.get("state")
   
    attendee.save()

    return {
        "entity": event
    }
