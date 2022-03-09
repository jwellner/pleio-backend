from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.translation import ugettext_lazy
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, INVALID_KEY
from core.lib import clean_graphql_input, tenant_schema, get_default_email_context
from core.tasks import send_mail_multi
from user.models import User

def resolve_handle_delete_account_request(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    performing_user = info.context["request"].user

    if not performing_user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not performing_user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    clean_input = clean_graphql_input(input)

    try:
        user_to_delete = User.objects.get(id=clean_input.get("guid"), is_delete_requested=True)
    except ObjectDoesNotExist:
        raise GraphQLError(INVALID_KEY)

    accepted = clean_input.get("accept", False)

    if accepted:
        is_deleted_user_admin = user_to_delete.has_role(USER_ROLES.ADMIN)
        language = user_to_delete.get_language()
        email_deleted_user = user_to_delete.email
        name_deleted_user = user_to_delete.name
        user_to_delete.delete()

        # Send email to user which is deleted
        context = get_default_email_context(performing_user)
        context['name_deleted_user'] = name_deleted_user

        translation.activate(language)
        subject = ugettext_lazy("Account of %(name_deleted_user)s removed") % {'name_deleted_user': name_deleted_user}

        send_mail_multi.delay(
            tenant_schema(),
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
                    tenant_schema(),
                    subject,
                    'email/admin_user_deleted.html',
                    context,
                    admin_user.email,
                    language=admin_user.get_language()
                )

    else:
        user_to_delete.is_delete_requested = False
        user_to_delete.save()

    return {
        "success": True
    }
