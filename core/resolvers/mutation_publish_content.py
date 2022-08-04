from core.models import Revision
from core.lib import clean_graphql_input
from core.resolvers import shared
from core.utils.entity import load_entity_by_id


def resolve_publish_content(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    entity = load_entity_by_id(input['guid'], ['core.Entity'])
    shared.assert_write_access(entity, user)

    if clean_input.get("revisionGuid"):
        revision = Revision.objects.get(id=clean_input.get("revisionGuid"))
    else:
        revision = entity.last_revision
    revision.description = clean_input.get("description")
    revision.save()

    shared.resolve_apply_revision(entity, revision)
    entity.save()

    return {
        "success": True
    }
