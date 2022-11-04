from graphql import GraphQLError

from core.constances import NOT_LOGGED_IN, USER_ROLES
from core.lib import clean_graphql_input
from core.resolvers import shared
from core.utils.entity import load_entity_by_id

from ..models import Task


def resolve_add_task(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    group = shared.get_group(clean_input)

    shared.assert_group_member(user, group)

    entity = Task()

    entity.owner = user

    if group:
        entity.group = group

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_add_access_id(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)

    shared.update_publication_dates(entity, clean_input)

    entity.save()


    return {
        "entity": entity
    }


def resolve_edit_task(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user
    entity = load_entity_by_id(input['guid'], [Task])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_access_id(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)
    shared.update_updated_at(entity)

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        shared.resolve_update_group(entity, clean_input)
        shared.resolve_update_owner(entity, clean_input)
        shared.resolve_update_time_created(entity, clean_input)

    entity.save()

    return {
        "entity": entity
    }


def resolve_edit_task_state(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    entity = load_entity_by_id(input['guid'], [Task])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    resolve_update_state(entity, clean_input)

    entity.save()

    return {
        "entity": entity
    }

def resolve_update_state(entity, clean_input):
    if 'state' in clean_input:
        entity.state = clean_input.get("state")
