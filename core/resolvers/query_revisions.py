from core.models import Entity, Revision
from graphql import GraphQLError
from core.constances import NOT_LOGGED_IN

def resolve_revisions(
        _,
        info,
        objectGuid,
        offset=0,
        limit=20,
):
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    entity = Entity.objects.get(id=objectGuid)
    if not entity.can_write(user):
        return {
            'total' : 0,
            'edges' : []
        }

    revisions = Revision.objects.get_queryset()
    revisions = revisions.filter(object=objectGuid)

    edges = revisions[offset:offset + limit]

    return {
        'total' : revisions.count(),
        'edges' : edges,
    }