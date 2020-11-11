from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy
from core.models import Group, GroupMembership
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE, USER_NOT_MEMBER_OF_GROUP
from core.lib import remove_none_from_dict, get_base_url, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_change_group_role(_, info, input):
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

    try:
        changing_user = User.objects.get(id=clean_input.get("userGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.is_member(changing_user):
        raise GraphQLError(USER_NOT_MEMBER_OF_GROUP)

    if clean_input.get("role") not in ['owner', 'admin', 'member', 'removed']:
        raise GraphQLError(COULD_NOT_SAVE)

    if clean_input.get("role") == "owner":
        schema_name = parse_tenant_config_path("")
        subject = ugettext_lazy("Ownership of the %(group_name)s group has been transferred") % {'group_name':group.name}
        link = get_base_url(info.context['request']) + "/groups/view/{}/{}".format(group.guid, slugify(group.name))

        context = get_default_email_context(info.context['request'])
        context['link'] = link
        context['group_name'] = group.name

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
        send_mail_multi.delay(schema_name, subject, 'email/group_ownership_transferred.html', context, changing_user.email)

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
