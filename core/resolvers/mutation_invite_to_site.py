from graphql import GraphQLError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import validate_email
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy
from core.models import SiteInvitation
from core import config
from core.constances import NOT_LOGGED_IN, INVALID_EMAIL, USER_NOT_SITE_ADMIN, USER_ROLES
from core.lib import remove_none_from_dict, get_base_url, generate_code, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def validate_email_addresses(email_addresses):
    if not email_addresses:
        return False
    for email in email_addresses:
        try:
            validate_email(email)
        except ValidationError:
            return False
    return True

def resolve_invite_to_site(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    email_addresses = clean_input.get("emailAddresses")

    if not validate_email_addresses(email_addresses):
        raise GraphQLError(INVALID_EMAIL)

    site_name = config.NAME

    for email in email_addresses:
        code = generate_code()
        try:
            invite = SiteInvitation.objects.get(email=email)
            invite.code = code
            invite.save()
        except ObjectDoesNotExist:
            invite = SiteInvitation.objects.create(email=email, code=code)

        subject = ugettext_lazy("You are invited to join site %(site_name)s") % {'site_name': site_name}
        url = get_base_url(info.context['request']) + '/login?invitecode='

        try:
            schema_name = parse_tenant_config_path("")
            context = get_default_email_context(info.context['request'])
            link = url + code
            context['link'] = link
            context['message'] = ""
            if 'message' in clean_input:
                context['message'] = format_html(clean_input.get('message'))
            send_mail_multi.delay(schema_name, subject, 'email/invite_to_site.html', context, email)
        except Exception:
            # TODO: logging
            raise Exception

    return {
        "success": True
    }
