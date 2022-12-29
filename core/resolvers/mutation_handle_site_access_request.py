from django.utils.timezone import now
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist

from core.mail_builders.site_access_request_accepted import schedule_site_access_request_accepted_mail
from core.mail_builders.site_access_request_denied import schedule_site_access_request_denied_mail
from core.models import SiteAccessRequest
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES
from core.lib import clean_graphql_input


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

    if not clean_input.get("silent", False):
        if accepted:
            schedule_site_access_request_accepted_mail(sender=user,
                                                       name=access_request.claims.get('name'),
                                                       email=access_request.claims.get('email'))
        else:
            schedule_site_access_request_denied_mail(sender=user,
                                                     name=access_request.claims.get('name'),
                                                     email=access_request.claims.get('email'))

    if accepted:
        access_request.accepted = True
        access_request.updated_at = now()
        access_request.save()
    else:
        access_request.delete()

    return {
        "success": True
    }
