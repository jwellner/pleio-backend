from cms.models import Page
from core.lib import clean_graphql_input
from core.resolvers import shared
from core.utils.entity import load_entity_by_id


def resolve_edit_page(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    user = info.context["request"].user
    entity: Page = load_entity_by_id(input['guid'], [Page])

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)
    shared.assert_write_access(entity, user)

    revision = shared.resolve_start_revision(entity, user)

    shared.resolve_update_tags(entity, clean_input)
    shared.resolve_update_access_id(entity, clean_input)
    shared.resolve_update_title(entity, clean_input)
    shared.resolve_update_rich_description(entity, clean_input)
    shared.update_publication_dates(entity, clean_input)

    entity.save()
    shared.store_update_revision(revision, entity)

    return {
        "entity": entity
    }
