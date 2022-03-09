from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.translation import ugettext_lazy
from core.constances import NOT_LOGGED_IN, COULD_NOT_DELETE, COULD_NOT_FIND, USER_ROLES
from core.lib import clean_graphql_input, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path
from user.models import User

def resolve_delete_user(_, info, input):
    # pylint: disable=redefined-builtin
    performing_user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not performing_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not performing_user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(COULD_NOT_DELETE)

    try:
        user = User.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    schema_name = parse_tenant_config_path("")
    language = user.get_language()
    is_deleted_user_admin = user.has_role(USER_ROLES.ADMIN)
    email_deleted_user = user.email
    name_deleted_user = user.name
    user.delete()

    # Send email to user which is deleted
    context = get_default_email_context(performing_user)
    context['name_deleted_user'] = name_deleted_user

    translation.activate(language)
    subject = ugettext_lazy("Account of %(name_deleted_user)s removed") % {'name_deleted_user': name_deleted_user}

    send_mail_multi.delay(
        schema_name,
        subject,
        'email/admin_user_deleted.html',
        context,
        email_deleted_user,
        language=language
    )

    # Send email to admins if user which is deleted is also an admin
    if is_deleted_user_admin:
        admin_users = User.objects.filter(roles__contains=['ADMIN'])
        for admin_user in admin_users:
            translation.activate(admin_user.get_language())
            subject = ugettext_lazy("A site administrator was removed from %(site_name)s") % {'site_name': context["site_name"]}
            send_mail_multi.delay(
                schema_name,
                subject,
                'email/admin_user_deleted.html',
                context,
                admin_user.email,
                language=admin_user.get_language()
            )

    return {
        'success': True
    }
