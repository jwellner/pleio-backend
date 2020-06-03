from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Subgroup
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict

def resolve_edit_subgroup(_, info, input):
    # pylint: disable=redefined-builtin
    # TODO: alter graphql schema to make groupGuid and name required

    user = info.context.user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    id = clean_input.get("id")

    try:
        subgroup = Subgroup.objects.get(id=id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not subgroup.group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    members = []
    if 'members' in clean_input:
        for member in clean_input.get("members"):
            try:
                user = User.objects.get(id=member)
            except ObjectDoesNotExist:
                raise GraphQLError(COULD_NOT_FIND)
            # member of subgroup must be member of group
            group_ids = user.memberships.filter(type__in=('member', 'admin', 'owner')).values_list('group', flat=True)
            if subgroup.group.id not in group_ids:
                raise GraphQLError(COULD_NOT_SAVE)
            members.append(user)

    if 'name' in clean_input:
        subgroup.name = clean_input.get("name")

    subgroup.save()

    subgroup_members = subgroup.members.all()
    # add members not currently in subgroup
    add_members = [x for x in members if x not in subgroup_members]

    # remove members not in members argument which exist in subgroup
    remove_members = [x for x in subgroup_members if x not in members]

    for member in add_members:
        subgroup.members.add(member)
    for member in remove_members:
        subgroup.members.remove(member)

    return {
        "success": True
    }
