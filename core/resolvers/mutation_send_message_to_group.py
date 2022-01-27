from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from core.models import Group
from user.models import User
from django.utils import timezone, translation
from django.utils.translation import ugettext_lazy
from django.utils.html import format_html
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, get_default_email_context
from datetime import timedelta
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_send_message_to_group(_, info, input):
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

    # threshold for deciding inactive user
    threshold = timezone.now() - timedelta(hours=4460)

    receiving_users = []

    if clean_input.get('isTest'):
        receiving_users = [user]
    elif clean_input.get('sendToAllMembers'):
        receiving_users = User.objects.filter(memberships__group__in=[group], is_active=True, _profile__last_online__gte=threshold)
    else:
        for guid in clean_input.get('recipients'):
            try:
                receiving_user = User.objects.get(id=guid, is_active=True, _profile__last_online__gte=threshold)
                if not group.is_member(receiving_user):
                    continue
            except ObjectDoesNotExist:
                continue
            receiving_users.append(receiving_user)

    context = get_default_email_context(user)
    schema_name = parse_tenant_config_path("")
    context['message'] = format_html(clean_input.get('message'))

    for receiving_user in receiving_users:
        translation.activate(receiving_user.get_language())
        subject = ugettext_lazy("Message from group {0}: {1}").format(group.name, clean_input.get('subject'))
        send_mail_multi.delay(
            schema_name,
            subject,
            'email/send_message_to_group.html',
            context,
            receiving_user.email,
            language=receiving_user.get_language()
        )

    if clean_input.get('sendCopyToSender', False) and user not in receiving_users:
        translation.activate(user.get_language())
        subject = ugettext_lazy("Copy: Message from group {0}: {1}").format(group.name, clean_input.get('subject'))
        send_mail_multi.delay(
            schema_name,
            subject,
            'email/send_message_to_group.html',
            context,
            user.email,
            language=user.get_language()
        )

    return {
          'group': group
    }
