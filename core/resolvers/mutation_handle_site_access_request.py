from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from core.models import SiteAccessRequest
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES
from core.lib import clean_graphql_input, tenant_schema, get_default_email_context
from core.tasks import send_mail_multi
from core import config

def resolve_handle_site_access_request(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    clean_input = clean_graphql_input(input)

    try:
        access_request = SiteAccessRequest.objects.get(email=clean_input.get("email"))
    except ObjectDoesNotExist:
        return {
            "success": False
        }

    accepted = clean_input.get("accept")
    silent = clean_input.get("silent", False)

    if not silent:
        context = get_default_email_context(user)
        context['request_name'] = access_request.claims.get('name')

        if accepted:
            subject = ugettext_lazy("You are now member of: %(site_name)s") % {'site_name': config.NAME }
            context['intro'] = config.SITE_MEMBERSHIP_ACCEPTED_INTRO
            send_mail_multi.delay(tenant_schema(), subject, 'email/site_access_request_accepted.html', context, access_request.claims.get('email'))
        else:
            subject = ugettext_lazy("Membership request declined for: %(site_name)s") % {'site_name': config.NAME }
            context['intro'] = config.SITE_MEMBERSHIP_DENIED_INTRO
            send_mail_multi.delay(tenant_schema(), subject, 'email/site_access_request_denied.html', context, access_request.claims.get('email'))

    if accepted:
        access_request.accepted=True
        access_request.save()
    else:
        access_request.delete()

    return {
        "success": True
    }
