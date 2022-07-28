from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from core.constances import COULD_NOT_FIND_GROUP
from core.lib import clean_graphql_input
from core.models import Group
from core.resolvers import shared
from event.resolvers import shared as event_shared
from event.models import Event


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

    event_shared.resolve_update_startenddate(entity, clean_input)
    event_shared.resolve_update_source(entity, clean_input)
    event_shared.resolve_update_location(entity, clean_input)
    event_shared.resolve_update_max_attendees(entity, clean_input)
    event_shared.resolve_update_ticket_link(entity, clean_input)
    event_shared.resolve_update_rsvp(entity, clean_input)
    event_shared.resolve_update_attend_without_account(entity, clean_input)
    event_shared.resolve_update_qr_access(entity, clean_input)

    entity.save()
    entity.add_follow(user)

    event_shared.resolve_update_slots_available(entity, clean_input)

    return {
        "entity": entity
    }
