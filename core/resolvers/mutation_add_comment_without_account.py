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

    CommentRequest.objects.create(
        code=code,
        email=email,
        name=name,
        container=entity,
        description=input.get("description", ""),
        rich_description=input.get("richDescription")
    )

    confirm_url = get_base_url() + '/comment/confirm/' + entity.guid + '?email=' + email + '&code=' + code

    context = get_default_email_context()
    context['confirm_url'] = confirm_url
    context['comment'] = input.get("description", "")
    context['entity_title'] = entity.title
    context['entity_url'] = get_base_url() + entity.url

    subject = ugettext_lazy("Confirm comment on %(site_name)s") % {'site_name': context["site_name"]}

    send_mail_multi.delay(tenant_schema(), subject, 'email/confirm_add_comment_without_account.html', context, email)

    return {
        'success': True
    }
