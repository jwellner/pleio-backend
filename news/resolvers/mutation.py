from graphql import GraphQLError

from core.constances import COULD_NOT_ADD, USER_ROLES
from core.lib import clean_graphql_input
from core.resolvers import shared
from core.utils.entity import load_entity_by_id
from news.models import News


def resolve_add_news(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    if not (user.has_role(USER_ROLES.ADMIN) or user.has_role(USER_ROLES.EDITOR)):
        raise GraphQLError(COULD_NOT_ADD)

    group = shared.get_group(clean_input)

    shared.assert_group_member(user, group)

    entity = News()

    entity.owner = user
    entity.group = group

    shared.resolve_add_access_id(entity, clean_input)
    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)
    shared.update_featured_image(entity, clean_input)
    shared.resolve_add_suggested_items(entity, clean_input)

    shared.update_publication_dates(entity, clean_input)
    shared.update_is_featured(entity, user, clean_input)

    resolve_update_source(entity, clean_input)

    entity.save()
    shared.store_initial_revision(entity)

    entity.add_follow(user)


    return {
        "entity": entity
    }


def resolve_edit_news(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    user = info.context["request"].user
    entity = load_entity_by_id(input['guid'], [News])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    revision = shared.resolve_start_revision(entity, user)

    shared.resolve_update_access_id(entity, clean_input)
    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.resolve_update_abstract(entity, clean_input)
    shared.update_featured_image(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)
    shared.update_is_featured(entity, user, clean_input)
    shared.update_publication_dates(entity, clean_input)
    shared.resolve_update_suggested_items(entity, clean_input)

    resolve_update_source(entity, clean_input)

    # only admins can edit these fields
    if user.has_role(USER_ROLES.ADMIN):
        shared.resolve_update_owner(entity, clean_input)
        shared.resolve_update_time_created(entity, clean_input)


    entity.save()
    shared.store_update_revision(revision, entity)

    return {
        "entity": entity
    }


def resolve_update_source(entity, clean_input):
    if 'source' in clean_input:
        entity.source = clean_input.get("source")
