from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import remove_none_from_dict, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, COULD_NOT_FIND_GROUP, USER_ROLES
from core.models import Group
from ..models import Discussion

def resolve_add_discussion(_, info, input):
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

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    entity.save()

    entity.add_follow(user)

    return {
        "entity": entity
    }


def resolve_edit_discussion(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Discussion.objects.get(id=clean_input.get("guid"))
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

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    entity.save()

    return {
        "entity": entity
    }
