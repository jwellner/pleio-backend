from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_toggle_user_is_admin(_, info, input):
    # pylint: disable=redefined-builtin

    performing_user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not performing_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not performing_user.is_admin:
        raise GraphQLError(COULD_NOT_SAVE)

    try:
        user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    schema_name = parse_tenant_config_path("")
    context = get_default_email_context(info.context['request'])
    context['name_of_user_admin_role_changed'] = user.name
    context['link'] = context['site_url'] + user.url

    if user.is_admin:
        user.is_admin = False
        user.save()

        admin_email_addresses = list(User.objects.filter(is_admin=True).values_list('email', flat=True))
        subject = ugettext_lazy("A site administrator was removed from %(site_name)s") % {'site_name': context["site_name"]}

        # mail to admins to notify about removed admin
        for admin_email_address in admin_email_addresses:
            send_mail_multi.delay(schema_name, subject, 'email/user_role_admin_removed_for_admins.html', context, admin_email_address)

        subject = ugettext_lazy("Your site administrator rights for %(site_name)s were removed") % {'site_name': context["site_name"]}

        # mail to user to notify about removed rigths
        send_mail_multi.delay(schema_name, subject, 'email/user_role_admin_removed_for_user.html', context, user.email)

    else:
        admin_email_addresses = list(User.objects.filter(is_admin=True).values_list('email', flat=True))

        user.is_admin = True
        user.save()

        subject = ugettext_lazy("A new site administrator was assigned for %(site_name)s") % {'site_name': context["site_name"]}
        # mail to admins to notify about added admin
        for admin_email_address in admin_email_addresses:
            send_mail_multi.delay(schema_name, subject, 'email/user_role_admin_assigned_for_admins.html', context, admin_email_address)

        subject = ugettext_lazy("You're granted site administrator right on %(site_name)s") % {'site_name': context["site_name"]}

        # mail to user to notify about added rigths
        send_mail_multi.delay(schema_name, subject, 'email/user_role_admin_assigned_for_user.html', context, user.email)

    return {
        'success': True
    }
