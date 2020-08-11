from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from core.models import GroupInvitation
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_INVITE
from core.lib import remove_none_from_dict, send_mail_multi, get_base_url, get_default_email_context

def resolve_resend_group_invitation(_, info, input):
    # pylint: disable=redefined-builtin
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        invitation = GroupInvitation.objects.get(id=clean_input.get("id"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)
    group = invitation.group

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_INVITE)

    subject = ugettext_lazy("Reminder to become a member of the %(group_name)s group") % {'group_name': group.name}
    link = get_base_url(info.context['request']) + '/groups/invitations/?invitecode=' + invitation.code

    try:
        context = get_default_email_context(info.context['request'])
        context['link'] = link
        context['group_name'] = group.name

        email = send_mail_multi(subject, 'email/resend_group_invitation.html', context, [invitation.invited_user.email])
        email.send()
    except Exception:
        # TODO: logging
        pass

    return {
        "group": group
    }
