from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.group_message import schedule_group_message_mail
from core.models import Group, Subgroup
from user.models import User
from django.utils import timezone
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input
from datetime import timedelta


def resolve_send_message_to_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    # threshold for deciding inactive user
    threshold = timezone.now() - timedelta(hours=4460)

    receiving_users = []

    if clean_input.get('isTest'):
        receiving_users = [user]
    elif clean_input.get('sendToAllMembers'):
        receiving_users = User.objects.filter(memberships__group__in=[group], is_active=True,
                                              _profile__last_online__gte=threshold)
    else:
        if clean_input.get('subGroup'):
            subgroup = Subgroup.objects.get(id=clean_input.get('subGroup'))
            receiving_users.extend([member for member in subgroup.members.all() if group.is_member(member)])

        for guid in (clean_input.get('recipients') or []):
            try:
                receiving_user = User.objects.get(id=guid, is_active=True, _profile__last_online__gte=threshold)
                if not group.is_member(receiving_user):
                    continue
            except ObjectDoesNotExist:
                continue
            receiving_users.append(receiving_user)

    for receiving_user in receiving_users:
        schedule_group_message_mail(message=clean_input.get('message'),
                                    subject=clean_input.get('subject'),
                                    receiver=receiving_user,
                                    sender=user,
                                    group=group,
                                    copy=False)

    if bool(clean_input.get('sendCopyToSender')) and user not in receiving_users:
        schedule_group_message_mail(message=clean_input.get('message'),
                                    subject=clean_input.get('subject'),
                                    receiver=user,
                                    sender=user,
                                    group=group,
                                    copy=True)

    return {
        'group': group
    }
