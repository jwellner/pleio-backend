from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from core.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, send_mail_multi


def resolve_toggle_request_delete_user(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        requested_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not requested_user == user:
        raise GraphQLError(COULD_NOT_SAVE)

    if user.is_delete_requested:
        user.is_delete_requested = False
        user.save()

        subject = ugettext_lazy("Request to remove account cancelled")
        context = {'username': user.name}

        email = send_mail_multi(subject, 'email/toggle_request_delete_user_cancelled.html', context, [user.email])

    else:
        user.is_delete_requested = True
        user.save()

        subject = ugettext_lazy("Request to remove account")
        context = {'username': user.name}

        email = send_mail_multi(subject, 'email/toggle_request_delete_user_requested.html', context, [user.email])

    email.send()

    return {
          "guid": None
    }
