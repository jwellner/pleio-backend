from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import remove_none_from_dict, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_send_message_to_user(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        receiving_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    context = get_default_email_context(info.context['request'])
    context['message'] = format_html(clean_input.get('message'))
    schema_name = parse_tenant_config_path("")

    subject = ugettext_lazy("Message from {0}: {1}").format(user.name, clean_input.get('subject'))

    send_mail_multi.delay(schema_name, subject, 'email/send_message_to_user.html', context, receiving_user.email)

    return {
          "success": True
    }
