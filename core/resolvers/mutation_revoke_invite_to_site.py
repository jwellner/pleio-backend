from graphql import GraphQLError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from core.models import SiteInvitation
from core.constances import NOT_LOGGED_IN, INVALID_EMAIL, USER_NOT_SITE_ADMIN
from core.lib import remove_none_from_dict


def validate_email_addresses(email_addresses):
    if not email_addresses:
        return False
    for email in email_addresses:
        try:
            validate_email(email)
        except ValidationError:
            return False
    return True

def resolve_revoke_invite_to_site(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.is_admin:
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    email_addresses = clean_input.get("emailAddresses")

    if not validate_email_addresses(email_addresses):
        raise GraphQLError(INVALID_EMAIL)

    for email in email_addresses:
        try:
            SiteInvitation.objects.get(email=email).delete()
        except Exception:
            continue

    return {
        "success": True
    }
