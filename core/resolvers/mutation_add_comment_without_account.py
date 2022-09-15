from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from core.lib import generate_code
from core.constances import COULD_NOT_FIND, COULD_NOT_ADD, INVALID_EMAIL, INVALID_VALUE
from core.mail_builders.comment_without_account import schedule_comment_without_account_mail
from core.models import Entity, CommentRequest
from core import config


def resolve_add_comment_without_account(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user

    email = input.get("email", None)
    name = input.get("name", None)

    if user.is_authenticated:
        raise GraphQLError(COULD_NOT_ADD)

    if not config.COMMENT_WITHOUT_ACCOUNT_ENABLED:
        raise GraphQLError(COULD_NOT_ADD)

    try:
        validate_email(email)
    except ValidationError:
        raise GraphQLError(INVALID_EMAIL)

    if not name:
        raise GraphQLError(INVALID_VALUE)

    try:
        entity = Entity.objects.get_subclass(id=input.get("containerGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not entity.can_read(user):
        GraphQLError(COULD_NOT_ADD)

    code = generate_code()
    comment_request = CommentRequest.objects.create(
        code=code,
        email=email,
        name=name,
        container=entity,
        rich_description=input.get("richDescription")
    )

    schedule_comment_without_account_mail(comment_request=comment_request,
                                          entity=entity)

    return {
        'success': True
    }
