from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group, GroupMembership
from user.models import User
from django.utils.translation import ugettext_lazy
from core.constances import NOT_LOGGED_IN, COULD_NOT_SAVE, COULD_NOT_FIND
from core.lib import remove_none_from_dict, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path


def resolve_reject_site_membership_request(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("groupGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    try:
        requesting_user = User.objects.get(id=clean_input.get("userGuid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        membership_request = GroupMembership.objects.get(user=requesting_user, group=group)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    membership_request.delete()

    subject = ugettext_lazy("Request for access to the %(group_name)s group has been refused") % {'group_name': group.name}

    schema_name = parse_tenant_config_path("")
    context = get_default_email_context(info.context['request'])
    context['group_name'] = group.name

    send_mail_multi.delay(schema_name, subject, 'email/reject_membership_request.html', context, requesting_user.email)

    return {
        "group": group
    }
