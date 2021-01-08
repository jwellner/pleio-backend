from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateparse
from core.lib import remove_none_from_dict, access_id_to_acl
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND_GROUP, COULD_NOT_FIND, COULD_NOT_SAVE, USER_ROLES, INVALID_DATE
from core.models import Group
from user.models import User
from wiki.models import Wiki

def resolve_add_wiki(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    group = None
    parent = None

    if 'containerGuid' in clean_input:
        try:
            group = Group.objects.get(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            try:
                parent = Wiki.objects.get_subclass(id=clean_input.get("containerGuid"))
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND_GROUP)

    if parent and parent.group:
        group = parent.group

    if group and not group.is_full_member(user) and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError("NOT_GROUP_MEMBER")

    # default fields for all entities
    entity = Wiki()

    entity.owner = user
    entity.tags = clean_input.get("tags")

    entity.group = group
    entity.parent = parent

    entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))
    entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    entity.title = clean_input.get("title")
    entity.description = clean_input.get("description")
    entity.rich_description = clean_input.get("richDescription")

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    entity.save()

    return {
        "entity": entity
    }

def resolve_edit_wiki(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Wiki.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    if 'title' in clean_input:
        entity.title = clean_input.get("title")
    if 'description' in clean_input:
        entity.description = clean_input.get("description")
    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")

    if 'containerGuid' in clean_input:
        try:
            container = Wiki.objects.get_subclass(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            GraphQLError(COULD_NOT_FIND)

        entity.parent = container
        entity.group = container.group

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        if 'groupGuid' in input:
            if input.get("groupGuid") is None:
                entity.group = None
            else:
                try:
                    group = Group.objects.get(id=clean_input.get("groupGuid"))
                    entity.group = group
                except ObjectDoesNotExist:
                    raise GraphQLError(COULD_NOT_FIND)

        if 'ownerGuid' in clean_input:
            try:
                owner = User.objects.get(id=clean_input.get("ownerGuid"))
                entity.owner = owner
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)

        if 'timeCreated' in clean_input:
            try:
                created_at = dateparse.parse_datetime(clean_input.get("timeCreated"))
                entity.created_at = created_at
            except ObjectDoesNotExist:
                raise GraphQLError(INVALID_DATE)

    entity.save()

    return {
        "entity": entity
    }
