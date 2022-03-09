from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html
from django.utils import translation
from django.utils.translation import ugettext_lazy
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import clean_graphql_input, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_send_message_to_user(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        receiving_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    context = get_default_email_context(user)
    context['message'] = format_html(clean_input.get('message'))
    schema_name = parse_tenant_config_path("")

    translation.activate(receiving_user.get_language())
    subject = ugettext_lazy("Message from {0}: {1}").format(user.name, clean_input.get('subject'))
    context['subject'] = subject

    send_mail_multi.delay(
        schema_name, subject,
        'email/send_message_to_user.html',
        context,
        receiving_user.email,
        language=receiving_user.get_language()
    )

    if clean_input.get('sendCopyToSender', False):
        translation.activate(user.get_language())
        subject = ugettext_lazy("Copy: Message from {0}: {1}").format(user.name, clean_input.get('subject'))
        send_mail_multi.delay(
            schema_name,
            subject,
            'email/send_message_to_user.html',
            context,
            user.email,
            language=user.get_language()
        )

    return {
          "success": True
    }
