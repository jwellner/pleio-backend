from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy
from core.models import User, Group, GroupMembership
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_NOT_MEMBER_OF_GROUP
from core.lib import remove_none_from_dict, send_mail_multi, get_base_url

def resolve_change_group_role(_, info, input):
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

    try:
        changing_user = User.objects.get(id=clean_input.get("userGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.is_member(changing_user):
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    if clean_input.get("role") not in ['owner', 'admin', 'member', 'removed']:
        raise GraphQLError(COULD_NOT_SAVE)

    if clean_input.get("role") == "owner":
        subject = ugettext_lazy("Ownership of the %s group has been transferred" % group.name)
        link = get_base_url(info.context) + "/groups/view/{}/{}".format(group.guid, slugify(group.name))
        context = {'link': link, 'group_name': group.name, 'user_name': user.name}
        email = send_mail_multi(subject, 'email/group_ownership_transferred.html', context, [changing_user.email])

        changing_user_membership = GroupMembership.objects.get(group=group, user=changing_user)
        changing_user_membership.type = 'owner'
        changing_user_membership.save()
        group.owner = changing_user
        group.save()
        try:
            user_membership = GroupMembership.objects.get(group=group, user=user)
            user_membership.type = 'admin'
            user_membership.save()
        except ObjectDoesNotExist:
            pass
        email.send()

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