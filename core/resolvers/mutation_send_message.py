from graphql import GraphQLError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from core.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import remove_none_from_dict


def resolve_send_message_to_user(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        receiving_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    email = EmailMessage(
        clean_input.get('subject'),
        clean_input.get('message'),
        settings.FROM_EMAIL,
        [receiving_user.email],
        reply_to=[user.email]
    )

    result = email.send()

    return {
          "success": result
    }
