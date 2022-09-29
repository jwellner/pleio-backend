from graphql import GraphQLError

from core.constances import USER_ROLES
from core.lib import clean_graphql_input
from core.resolvers import shared
from core.utils.entity import load_entity_by_id

from ..models import Discussion


def resolve_add_discussion(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    group = shared.get_group(clean_input)

    shared.assert_group_member(user, group)

    entity = Discussion()

    entity.owner = user

    if group:
        entity.group = group
    
    shared.resolve_add_access_id(entity, clean_input)
    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)

    shared.update_featured_image(entity, clean_input)

    shared.update_is_featured(entity, user, clean_input)

    shared.update_publication_dates(entity, clean_input)

    entity.save()

    entity.add_follow(user)

    return {
        "entity": entity
    }


def resolve_edit_discussion(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user
    entity = load_entity_by_id(input['guid'], [Discussion])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)
    shared.resolve_update_tags(entity, clean_input)
    shared.update_featured_image(entity, clean_input)

    shared.update_is_featured(entity, user, clean_input)
    shared.resolve_update_access_id(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        shared.resolve_update_group(entity, clean_input)

        shared.resolve_update_owner(entity, clean_input)

        shared.resolve_update_time_created(entity, clean_input)

    entity.save()

    return {
        "entity": entity
    }
