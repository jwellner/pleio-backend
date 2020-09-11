from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from core.constances import NOT_LOGGED_IN, COULD_NOT_DELETE, COULD_NOT_FIND
from core.lib import remove_none_from_dict, get_default_email_context
from user.models import User
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_delete_user(_, info, input):
    # pylint: disable=redefined-builtin
    performing_user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not performing_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not performing_user.is_admin:
        raise GraphQLError(COULD_NOT_DELETE)

    try:
        user = User.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    schema_name = parse_tenant_config_path("")
    is_deleted_user_admin = user.is_admin
    email_deleted_user = user.email
    name_deleted_user = user.name
    user.delete()

    # Send email to user which is deleted
    context = get_default_email_context(info.context['request'])
    context['name_deleted_user'] = name_deleted_user
    subject = ugettext_lazy("Account of %(name_deleted_user)s removed") % {'name_deleted_user': name_deleted_user}

    send_mail_multi.delay(schema_name, subject, 'email/admin_user_deleted.html', context, email_deleted_user)

    # Send email to admins if user which is deleted is also an admin
    if is_deleted_user_admin:
        context = get_default_email_context(info.context['request'])
        context['name_deleted_user'] = performing_user.name
        subject = ugettext_lazy("A site administrator was removed from %(site_name)s") % {'site_name': context["site_name"]}

        admin_email_addresses = User.objects.filter(is_admin=True).values_list('email', flat=True)
        for email_address in admin_email_addresses:
            send_mail_multi.delay(schema_name, subject, 'email/admin_user_deleted.html', context, email_address)

    return {
        'success': True
    }
