from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from core.models import Group
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, get_base_url, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_accept_membership_request(_, info, input):
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

    if group.is_full_member(requesting_user):
        return {
            "group": group
        }

    schema_name = parse_tenant_config_path("")
    group.join(requesting_user, 'member')
    subject = ugettext_lazy("Request for access to the %(group_name)s group has been approved") % {'group_name': group.name}
    link = get_base_url(info.context['request']) + group.url

    context = get_default_email_context(info.context['request'])
    context['group_name'] = group.name
    context['link'] = link

    send_mail_multi.delay(schema_name, subject, 'email/accept_membership_request.html', context, requesting_user.email)

    return {
        "group": group
    }
