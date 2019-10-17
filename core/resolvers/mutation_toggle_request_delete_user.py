from graphql import GraphQLError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from core.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict


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
        email = EmailMessage(
            "Request to remove account cancelled",
            f"You, as <strong> {user.name} </strong> user, have cancelled your request to remove your account.",
            settings.FROM_EMAIL,
            [user.email]
        )
    else:
        user.is_delete_requested = True
        user.save()
        email = EmailMessage(
            "Request to remove account",
            f"""You, as user, <strong> {user.name} </strong> have requested that your account be removed. You will be informed once the website \
            administrator has done so.""",
            settings.FROM_EMAIL,
            [user.email]
        )

    email.send()

    return {
          "guid": None
    }
