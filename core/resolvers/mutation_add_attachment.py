from graphql import GraphQLError
from core.models import Attachment, AttachmentMixin
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

    # if contentGuid is present we can try to attach it directly to the content
    if input.get("contentGuid"):
        for subclass in AttachmentMixin.__subclasses__():
            content = subclass.objects.filter(id=input.get("contentGuid")).first()
            if content and content.can_write(user):
                attachment.attached = content
                attachment.save()
                break

    return {
        "attachment": attachment
    }
