from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.lib import clean_graphql_input, access_id_to_acl, tenant_schema
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND, COULD_NOT_FIND_GROUP, USER_ROLES
from core.models import Group
from core.resolvers import shared
from core.resolvers.shared import clean_abstract
from user.models import User
from ..models import Discussion


def resolve_add_discussion(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

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
    entity.rich_description = clean_input.get("richDescription")

    if 'abstract' in clean_input:
        abstract = clean_input.get("abstract")
        clean_abstract(abstract)
        entity.abstract = abstract

    shared.update_featured_image(entity, clean_input)

    if user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR):
        if 'isFeatured' in clean_input:
            entity.is_featured = clean_input.get("isFeatured")

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

    clean_input = clean_graphql_input(input)

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

    if 'richDescription' in clean_input:
        entity.rich_description = clean_input.get("richDescription")

    if 'abstract' in clean_input:
        abstract = clean_input.get("abstract")
        clean_abstract(abstract)
        entity.abstract = abstract

    if 'tags' in clean_input:
        entity.tags = clean_input.get("tags")

    if 'accessId' in clean_input:
        entity.read_access = access_id_to_acl(entity, clean_input.get("accessId"))

    if 'writeAccessId' in clean_input:
        entity.write_access = access_id_to_acl(entity, clean_input.get("writeAccessId"))

    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

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
            entity.created_at = clean_input.get("timeCreated")

    entity.save()

    return {
        "entity": entity
    }
