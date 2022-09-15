from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.user_send_message import schedule_user_send_message_mail
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import clean_graphql_input

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

    schedule_user_send_message_mail(message=clean_input.get('message'),
                                    subject=clean_input.get('subject'),
                                    receiver=receiving_user,
                                    sender=user)

    if clean_input.get('sendCopyToSender', False):
        schedule_user_send_message_mail(message=clean_input.get('message'),
                                        subject=clean_input.get('subject'),
                                        receiver=user,
                                        sender=user,
                                        copy=True)

    return {
          "success": True
    }
