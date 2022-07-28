from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, COULD_NOT_FIND_GROUP, USER_ROLES
from core.lib import clean_graphql_input
from core.models import Group
from core.resolvers import shared
from core.utils.entity import load_entity_by_id
from wiki.models import Wiki


def resolve_add_wiki(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

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
                parent = Wiki.objects.get_subclass(id=clean_input.get("containerGuid"))
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND_GROUP)

    if parent and parent.group:
        group = parent.group

    shared.assert_group_member(user, group)

    # default fields for all entities
    entity = Wiki()

    entity.owner = user
    entity.group = group
    entity.parent = parent

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_add_access_id(entity, clean_input)

    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)

    shared.resolve_update_abstract(entity, clean_input)

    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    shared.resolve_update_is_featured(entity, user, clean_input)

    entity.save()

    return {
        "entity": entity
    }


def resolve_edit_wiki(_, info, input, draft=False):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user
    entity = load_entity_by_id(input['guid'], [Wiki])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    shared.resolve_start_revision(entity)

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_access_id(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input, revision=True)
    shared.resolve_update_abstract(entity, clean_input)

    if 'containerGuid' in clean_input:
        try:
            container = Wiki.objects.get_subclass(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            GraphQLError(COULD_NOT_FIND)

        entity.parent = container
        entity.group = container.group

    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    shared.resolve_update_is_featured(entity, user, clean_input)

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        shared.resolve_update_group(entity, clean_input)

        shared.resolve_update_owner(entity, clean_input)

        shared.resolve_update_time_created(entity, clean_input)

    shared.resolve_store_revision(entity)

    if not draft:
        shared.resolve_apply_revision(entity, entity.last_revision)

    entity.save()

    return {
        "entity": entity
    }
