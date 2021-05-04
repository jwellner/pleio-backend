from graphql import GraphQLError
from core.models import Entity, Comment, Group, EntityAttachment, CommentAttachment, GroupAttachment # Group, Comment
from core.constances import NOT_LOGGED_IN, INVALID_CONTENT_GUID, COULD_NOT_ADD

def resolve_add_attachment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not input.get("file"):
        raise GraphQLError("NO_FILE")

    types = [Entity, Group, Comment] # Group, Comment

    for t in types:
        content = t.objects.filter(id=input.get("contentGuid")).first()
        if content:
            break

    if not content:
        raise GraphQLError(INVALID_CONTENT_GUID)

    if not content.can_write(user):
        raise GraphQLError(COULD_NOT_ADD)

    attachment = None

    if content._meta.object_name == 'Entity':
        attachment = EntityAttachment.objects.create(attached=content, upload=input.get("file"))
    if content._meta.object_name == 'Group':
        attachment = GroupAttachment.objects.create(attached=content, upload=input.get("file"))
    if content._meta.object_name == 'Comment':
        attachment = CommentAttachment.objects.create(attached=content, upload=input.get("file"))

    if not attachment:
        raise GraphQLError(COULD_NOT_ADD)

    return {
        "attachment": attachment
    }
