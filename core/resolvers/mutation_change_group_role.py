import logging

from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.group_change_ownership import schedule_change_group_ownership_mail
from core.models import Group, GroupMembership
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_NOT_MEMBER_OF_GROUP
from core.lib import clean_graphql_input

logger = logging.getLogger(__name__)


def resolve_change_group_role(_, info, input):
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

    try:
        changing_user = User.objects.get(id=clean_input.get("userGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.is_member(changing_user):
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    if clean_input.get("role") not in ['owner', 'admin', 'member', 'removed']:
        raise GraphQLError(COULD_NOT_SAVE)

    if clean_input.get("role") == "owner":
        changing_user_membership = GroupMembership.objects.get(group=group, user=changing_user)
        changing_user_membership.type = 'owner'
        changing_user_membership.save()
        previous_owner = group.owner
        group.owner = changing_user
        group.save()
        try:
            user_membership = GroupMembership.objects.get(group=group, user=previous_owner)
            user_membership.type = 'admin'
            user_membership.save()
        except ObjectDoesNotExist:
            pass

        schedule_change_group_ownership_mail(user=changing_user,
                                     sender=user,
                                     group=group)

    if clean_input.get("role") in ["member", "admin"]:
        try:
            user_membership = GroupMembership.objects.get(group=group, user=changing_user)
            user_membership.type = clean_input.get("role")
            user_membership.save()
        except ObjectDoesNotExist:
            pass

    if clean_input.get("role") == "removed":
        try:
            user_membership = GroupMembership.objects.get(group=group, user=changing_user)
            user_membership.delete()
        except ObjectDoesNotExist:
            pass

    return {
        "group": group
    }
