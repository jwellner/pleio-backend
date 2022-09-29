from graphql import GraphQLError

from core.constances import COULD_NOT_FIND
from core.models import Revision
from core.resolvers import shared


def resolve_update_revision(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    shared.assert_authenticated(user)

    revision = Revision.objects.filter(id=input.get('guid')).first()
    if not revision:
        raise GraphQLError(COULD_NOT_FIND)

    shared.assert_write_access(revision.container, user)

    revision.description = input.get("description")
    revision.save()

    return revision
