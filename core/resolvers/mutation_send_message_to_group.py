from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import User, Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, send_mail_multi


def resolve_send_message_to_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    email_addresses = []

    if clean_input.get('isTest'):
        email_addresses = [user.email]
    else:
        for guid in clean_input.get('recipients'):
            try:
                receiving_user = User.objects.get(id=guid)
                if not group.is_member(receiving_user):
                    continue
            except ObjectDoesNotExist:
                continue

            email_addresses.append(receiving_user.email)

    context = {'message': clean_input.get('message')}
    email = send_mail_multi(clean_input.get('subject'), 'email/send_message_to_group.html', context, email_addresses)
    email.send()

    return {
          'group': group
    }
