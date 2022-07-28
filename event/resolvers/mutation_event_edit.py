from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, USER_ROLES
from core.lib import clean_graphql_input
from core.resolvers import shared
from core.utils.entity import load_entity_by_id
from event.resolvers import shared as event_shared
from event.models import Event


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

            entity.parent = container
            entity.group = container.group

        except Event.DoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_access_id(entity, clean_input)

    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    shared.resolve_update_is_featured(entity, user, clean_input)

    event_shared.resolve_update_startenddate(entity, clean_input)
    event_shared.resolve_update_source(entity, clean_input)
    event_shared.resolve_update_location(entity, clean_input)
    event_shared.resolve_update_ticket_link(entity, clean_input)
    event_shared.resolve_update_max_attendees(entity, clean_input)
    event_shared.resolve_update_rsvp(entity, clean_input)
    event_shared.resolve_update_attend_without_account(entity, clean_input)
    event_shared.resolve_update_qr_access(entity, clean_input)
    event_shared.resolve_update_slots_available(entity, clean_input)

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        shared.resolve_update_group(entity, clean_input)

        shared.resolve_update_owner(entity, clean_input)

        shared.resolve_update_time_created(entity, clean_input)

    entity.save()

    return {
        "entity": entity
    }
