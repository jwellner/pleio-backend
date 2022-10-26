import logging

from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError

from core.constances import (COULD_NOT_FIND, COULD_NOT_SAVE,
                             USER_NOT_MEMBER_OF_GROUP)
from core.lib import clean_graphql_input
from core.models import Group, GroupMembership
from user.models import User
from core.resolvers import shared

logger = logging.getLogger(__name__)

def resolve_remove_group_members(_, info, input):
    # pylint: disable=redefined-builtin
    
    user = info.context["request"].user

    clean_input = clean_graphql_input(input)

    shared.assert_authenticated(user)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    shared.assert_write_access(group, user)

    guids = clean_input.get("userGuids")

    for guid in guids:
        try: 
            user_membership = GroupMembership.objects.get(group=group, user_id=guid)
            user_membership.delete()
        except ObjectDoesNotExist:
            pass

    return {
        "group": group
    }
