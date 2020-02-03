import reversion
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, COULD_NOT_FIND_GROUP
from core.models import Group
from ..models import Discussion

def resolve_add_discussion(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None

    if clean_input.get("containerGuid"):
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

    if group and not group.is_full_member(user) and not user.is_admin:
        raise GraphQLError("NOT_GROUP_MEMBER")

    with reversion.create_revision():
        entity = Discussion()

        entity.owner = user
        entity.tags = clean_input.get("tags")

        if group:
            entity.group = group

        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

        entity.title = clean_input.get("title")
        entity.description = clean_input.get("description")
        entity.rich_description = clean_input.get("richDescription")

        entity.save()

        entity.add_follow(user)

        reversion.set_user(user)
        reversion.set_comment("addEntity mutation")

    return {
        "entity": entity
    }


def resolve_edit_discussion(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not info.context.user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Discussion.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    with reversion.create_revision():

        entity.title = clean_input.get("title")
        entity.description = clean_input.get("description", "")
        entity.rich_description = clean_input.get("richDescription")

        entity.tags = clean_input.get("tags", [])
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId", 0))
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId", 0))

        entity.save()

        reversion.set_user(user)
        reversion.set_comment("editEntity mutation")

    return {
        "entity": entity
    }
