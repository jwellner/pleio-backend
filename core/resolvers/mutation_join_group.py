from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from core.models import Group
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, ALREADY_MEMBER_OF_GROUP
from core.lib import remove_none_from_dict, get_base_url, get_default_email_context, obfuscate_email, tenant_schema
from core.tasks import send_mail_multi

def resolve_join_group(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if group.is_full_member(user):
        raise GraphQLError(ALREADY_MEMBER_OF_GROUP)

    group_link = get_base_url() + group.url

    if (not group.is_closed and not group.is_membership_on_request) or group.can_write(user):
        group.join(user, 'member')
    else:
        group.join(user, 'pending')
        subject = ugettext_lazy("Access request for the %(group_name)s group") % {'group_name': group.name}
        context = get_default_email_context(user)
        context['link'] = group_link
        context['group_name'] = group.name
        context['user_obfuscated_email'] = obfuscate_email(user.email)

        receiving_members = group.members.filter(type__in=['admin', 'owner'])
        for receiving_member in receiving_members:
            send_mail_multi.delay(schema_name, subject, 'email/join_group.html', context, receiving_member.user.email)

    return {
        "group": group
    }
