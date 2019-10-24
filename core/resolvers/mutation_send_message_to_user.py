from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND
from core.lib import remove_none_from_dict, send_mail_multi


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

    context = {'message': clean_input.get('message')}

    email = send_mail_multi(clean_input.get('subject'), 'email/send_message_to_user.html', context, [receiving_user.email], [user.email])

    result = email.send()

    return {
          "success": result
    }
