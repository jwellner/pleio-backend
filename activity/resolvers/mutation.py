from graphql import GraphQLError

from core import config
from core.constances import COULD_NOT_ADD, USER_ROLES
from core.lib import access_id_to_acl, clean_graphql_input
from core.resolvers import shared
from core.utils.entity import load_entity_by_id

from ..models import StatusUpdate


# TODO: remove after fixed in frontend
def get_group_default_access_id(group):
    if group.is_closed:
        return 4

    return config.DEFAULT_ACCESS_ID


def resolve_add_status_update(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    group = shared.get_group(clean_input)

    shared.assert_group_member(user, group)

    if group and not group.is_submit_updates_enabled:
        raise GraphQLError(COULD_NOT_ADD)

    entity = StatusUpdate()

    entity.owner = user
    entity.tags = clean_input.get("tags", [])

    if group:
        entity.group = group

    resolve_update_access_id(entity, clean_input, group)

    shared.resolve_update_title(entity, clean_input)

    shared.resolve_update_rich_description(entity, clean_input)

    shared.update_publication_dates(entity, clean_input)

    entity.save()

    entity.add_follow(user)

    return {
        "entity": entity
    }


def resolve_edit_status_update(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user
    entity = load_entity_by_id(input['guid'], [StatusUpdate])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    shared.resolve_update_title(entity, clean_input)

    shared.resolve_update_rich_description(entity, clean_input)

    shared.resolve_update_tags(entity, clean_input)
    
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

def resolve_update_access_id(entity, clean_input, group): 
    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    else:
        if group:
            entity.read_access = access_id_to_acl(entity, get_group_default_access_id(group))
        else:
            entity.read_access = access_id_to_acl(entity, config.DEFAULT_ACCESS_ID)
    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))    
