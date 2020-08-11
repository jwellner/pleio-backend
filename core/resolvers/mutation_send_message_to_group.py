from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from user.models import User
from django.utils.translation import ugettext_lazy
from django.utils.html import format_html
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, send_mail_multi, get_default_email_context
from datetime import datetime, timedelta


def resolve_send_message_to_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    # threshold for deciding inactive user
    threshold = datetime.now() - timedelta(hours=4460)

    email_addresses = []

    if clean_input.get('isTest'):
        email_addresses = [user.email]
    elif clean_input.get('sendToAllMembers'):
        active_members = User.objects.filter(memberships__group__in=[group], is_active=True, _profile__last_online__gte=threshold)
        email_addresses = list(active_members.values_list('email', flat=True))
    else:
        for guid in clean_input.get('recipients'):
            try:
                receiving_user = User.objects.get(id=guid, is_active=True, _profile__last_online__gte=threshold)
                if not group.is_member(receiving_user):
                    continue
            except ObjectDoesNotExist:
                continue

            email_addresses.append(receiving_user.email)

    context = get_default_email_context(info.context['request'])
    context['message'] = format_html(clean_input.get('message'))

    subject = ugettext_lazy("Message from group {0}: {1}").format(group.name, clean_input.get('subject'))

    email = send_mail_multi(subject, 'email/send_message_to_group.html', context, email_addresses)
    email.send()

    return {
          'group': group
    }
