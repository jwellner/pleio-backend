from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy
from core.lib import generate_code, get_base_url, get_default_email_context, tenant_schema
from core.constances import COULD_NOT_FIND, COULD_NOT_ADD, INVALID_EMAIL, INVALID_VALUE
from core.models import Entity, CommentRequest
from core import config
from core.tasks import send_mail_multi


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

    from core.mail_builders.group_comment_without_account import submit_group_comment_without_account_mail
    submit_group_comment_without_account_mail(comment_request=comment_request,
                                              entity=entity)

    return {
        'success': True
    }
