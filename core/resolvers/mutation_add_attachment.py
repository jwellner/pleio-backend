import os

from graphql import GraphQLError

from core.models import AttachmentMixin
from core.constances import NOT_LOGGED_IN, COULD_NOT_ADD, FILE_NOT_CLEAN
from core.resolvers import shared
from file.models import FileFolder


def resolve_add_attachment(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not input.get("file"):
        raise GraphQLError("NO_FILE")

    attachment = FileFolder.objects.create(upload=input.get("file"),
                                           owner=user)

    shared.scan_file(attachment, delete_if_virus=True)

    if not attachment:
        raise GraphQLError(COULD_NOT_ADD)

    if attachment.refresh_read_access():
        attachment.save()

    shared.post_upload_file(attachment)

    # if contentGuid is present we can try to attach it directly to the content
    if input.get("contentGuid"):
        for subclass in AttachmentMixin.__subclasses__():
            content = subclass.objects.filter(id=input.get("contentGuid")).first()
            if content and content.can_write(user):
                content.attachments.create(file=attachment)
                break

    return {
        "attachment": attachment
    }
