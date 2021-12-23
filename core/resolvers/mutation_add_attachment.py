from graphql import GraphQLError
from core.models import Attachment
from core.constances import NOT_LOGGED_IN, COULD_NOT_ADD

def resolve_add_attachment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not input.get("file"):
        raise GraphQLError("NO_FILE")

    attachment = Attachment.objects.create(upload=input.get("file"), owner=user)

    if not attachment:
        raise GraphQLError(COULD_NOT_ADD)

    return {
        "attachment": attachment
    }
