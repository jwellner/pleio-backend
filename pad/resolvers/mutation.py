from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import COULD_NOT_SAVE, COULD_NOT_FIND
from core.lib import clean_graphql_input, access_id_to_acl
from core.models.group import Group
from core.resolvers import shared
from core import config
from file.models import FileFolder

def resolve_add_pad(_, info, input):
    # pylint: disable=redefined-builtin

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
                parent = FileFolder.objects.get(id=clean_input.get("containerGuid"))
                if not parent.can_write(user):
                    raise GraphQLError(COULD_NOT_SAVE)
                if not parent.group: # Only add to parent in group
                    raise GraphQLError("INVALID_CONTAINER_GUID")
                group = parent.group
            except ObjectDoesNotExist:
                if not clean_input.get("containerGuid") == user.guid:
                    raise GraphQLError("INVALID_CONTAINER_GUID")

    shared.assert_group_member(user, group)

    entity = FileFolder()
    entity.type = FileFolder.Types.PAD

    entity.owner = user
    entity.tags = clean_input.get("tags", [])

    if parent:
        entity.parent = parent

    if group:
        entity.group = group

    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_tags(entity, clean_input)

    default_access_id = 4 if group and group.is_closed else config.DEFAULT_ACCESS_ID

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId", default_access_id))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId", 0))

    entity.save()

    return {
        "entity": entity
    }


def resolve_edit_pad(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    try:
        entity = FileFolder.objects.filter(type=FileFolder.Types.PAD).get(id=input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_access_id(entity, clean_input)

    if clean_input.get("state"):
        entity.pad_state = clean_input.get("state")

    entity.save()

    return {
        "entity": entity
    }
