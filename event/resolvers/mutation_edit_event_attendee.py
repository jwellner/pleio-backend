from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from core.constances import ALREADY_CHECKED_IN, COULD_NOT_FIND, NOT_LOGGED_IN, COULD_NOT_SAVE
from core.lib import clean_graphql_input
from core.resolvers import shared
from event.models import Event

def resolve_edit_event_attendee(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument

    user = info.context["request"].user

    clean_input = clean_graphql_input(input, ["timeCheckedIn"])

    shared.assert_authenticated(user)

    try:
        event = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not event.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    attendee = event.get_attendee(clean_input.get("emailAddress"))
    if not attendee:
        raise GraphQLError(COULD_NOT_FIND)

    if 'timeCheckedIn' in clean_input:
        if attendee.checked_in_at is None:
            attendee.checked_in_at = clean_input.get("timeCheckedIn")
        elif clean_input.get("timeCheckedIn") is None:
            attendee.checked_in_at = None
        else:
            raise GraphQLError(ALREADY_CHECKED_IN)    

    attendee.updated_at = timezone.now()
    attendee.save()

    return {
        "entity": event
    }
