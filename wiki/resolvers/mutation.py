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

    shared.resolve_add_access_id(entity, clean_input)
    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)
    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)
    shared.update_is_featured(entity, user, clean_input)
    shared.resolve_add_suggested_items(entity, clean_input)

    entity.save()
    shared.store_initial_revision(entity)

    return {
        "entity": entity
    }


def resolve_edit_wiki(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user
    entity = load_entity_by_id(input['guid'], [Wiki])

    clean_input = clean_graphql_input(input, ['containerGuid'])

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    revision = shared.resolve_start_revision(entity, user)

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)
    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)
    shared.update_is_featured(entity, user, clean_input)
    shared.resolve_update_access_id(entity, clean_input)
    shared.resolve_update_suggested_items(entity, clean_input)
    shared.update_updated_at(entity)

    if 'containerGuid' in clean_input:
        container = None
        try:
            container = Wiki.objects.get_subclass(id=clean_input.get("containerGuid"))
        except ObjectDoesNotExist:
            GraphQLError(COULD_NOT_FIND)

        revision.content['parent'] = clean_input['containerGuid']

        entity.parent = container
        entity.group = container.group if container else None

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        shared.resolve_update_group(entity, clean_input)
        shared.resolve_update_owner(entity, clean_input)
        shared.resolve_update_time_created(entity, clean_input)

    entity.save()
    shared.store_update_revision(revision, entity)

    return {
        "entity": entity
    }
