from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_FIND_GROUP, COULD_NOT_SAVE, USER_ROLES
from core.lib import remove_none_from_dict, access_id_to_acl
from core.models import Group
from ..models import Task


def resolve_add_task(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None

    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND_GROUP)

    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError("NOT_GROUP_MEMBER")

    entity = Task()

    entity.owner = user
    entity.tags = clean_input.get("tags", [])

    if group:
        entity.group = group

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.title = clean_input.get("title", "")
    entity.description = clean_input.get("description", "")
    entity.rich_description = clean_input.get("richDescription", "")

    entity.save()

    return {
        "entity": entity
    }


def resolve_edit_task(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Task.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'title' in clean_input:
        entity.title = clean_input.get("title")
    if 'description' in clean_input:
        entity.description = clean_input.get("description")
    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")
    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.save()

    return {
        "entity": entity
    }


def resolve_edit_task_state(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Task.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'state' in clean_input:
        entity.state = clean_input.get("state")
    entity.save()

    return {
        "entity": entity
    }
