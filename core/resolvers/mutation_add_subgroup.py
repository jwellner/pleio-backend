from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group, Subgroup
from user.models import User
from core.constances import NOT_LOGGED_IN, INVALID_VALUE, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict

def resolve_add_subgroup(_, info, input):
    # pylint: disable=redefined-builtin
    # TODO: alter graphql schema to make groupGuid and name required
    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not clean_input.get("name"):
        raise GraphQLError(INVALID_VALUE)

    try:
        group = Group.objects.get(id=clean_input.get("groupGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    members = []
    if clean_input.get("members"):
        for member in clean_input.get("members"):
            try:
                user = User.objects.get(id=member)
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)
            # member of subgroup must be member of group
            group_ids = user.memberships.filter(type__in=('member', 'admin', 'owner')).values_list('group', flat=True)
            if group.id not in group_ids:
                raise GraphQLError(COULD_NOT_SAVE)
            members.append(user)

    subgroup = Subgroup()

    subgroup.name = clean_input.get("name")
    subgroup.group = group

    subgroup.save()

    for member in members:
        subgroup.members.add(member)

    return {
        "success": True
    }
