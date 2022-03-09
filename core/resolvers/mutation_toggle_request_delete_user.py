from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.translation import ugettext_lazy
from user.models import User
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_SAVE
from core.lib import clean_graphql_input, get_default_email_context, tenant_schema
from core.tasks import send_mail_multi

def resolve_toggle_request_delete_user(_, info, input):
    # pylint: disable=redefined-builtin

    user = info.context["request"].user
    clean_input = clean_graphql_input(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        requested_user = User.objects.get(id=clean_input.get('guid'))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not requested_user == user:
        raise GraphQLError(COULD_NOT_SAVE)

    context = get_default_email_context(user)

    language = requested_user.get_language()
    translation.activate(language)

    admin_users = User.objects.filter(roles__contains=['ADMIN'])

    if user.is_delete_requested:
        user.is_delete_requested = False
        user.save()

        subject = ugettext_lazy("Request to remove account cancelled")

        send_mail_multi.delay(
            tenant_schema(),
            subject,
            'email/toggle_request_delete_user_cancelled.html',
            context,
            user.email,
            language=language
        )

        # mail to admins to notify about removed admin
        for admin_user in admin_users:
            translation.activate(admin_user.get_language())
            subject = ugettext_lazy("Request to remove account cancelled")
            send_mail_multi.delay(
                tenant_schema(),
                subject,
                'email/toggle_request_delete_user_cancelled_admin.html',
                context,
                admin_user.email,
                language=admin_user.get_language()
            )

    else:
        user.is_delete_requested = True
        user.save()

        subject = ugettext_lazy("Request to remove account")

        send_mail_multi.delay(
            tenant_schema(),
            subject,
            'email/toggle_request_delete_user_requested.html',
            context,
            user.email,
            language=language
        )

        # mail to admins to notify about removed admin
        for admin_user in admin_users:
            translation.activate(admin_user.get_language())
            subject = ugettext_lazy("Request to remove account")
            send_mail_multi.delay(
                tenant_schema(),
                subject,
                'email/toggle_request_delete_user_requested_admin.html',
                context,
                admin_user.email,
                language=admin_user.get_language()
            )

    return {
          "viewer": user
    }
