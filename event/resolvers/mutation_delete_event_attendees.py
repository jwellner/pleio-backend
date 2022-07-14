from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import COULD_NOT_FIND
from core.lib import clean_graphql_input
from core.resolvers import shared
from event.resolvers import shared as event_shared
from event.models import Event


def resolve_delete_event_attendees(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    try:
        event = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    shared.assert_write_access(event, user)

    for email_address in clean_input.get("emailAddresses"):
        attendee = event.get_attendee(email_address)
        if not attendee:
            continue

        event_shared.resolve_delete_attendee(attendee)

    return {
        "entity": event
    }
