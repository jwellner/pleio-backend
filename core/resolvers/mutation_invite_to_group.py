from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.translation import ugettext_lazy
from core.models import Group, GroupInvitation
from user.models import User
from core import config
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, COULD_NOT_INVITE, USER_NOT_SITE_ADMIN, USER_ROLES
from core.lib import remove_none_from_dict, get_base_url, generate_code, get_default_email_context
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_invite_to_group(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    user = info.context["request"].user
    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        group = Group.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not group.can_write(user):
        raise GraphQLError(COULD_NOT_INVITE)

    if clean_input.get("directAdd") and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    if clean_input.get("addAllUsers") and not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    # Add all users without sending email
    if clean_input.get("addAllUsers"):
        users = User.objects.filter(is_active=True)
        for u in users:
            if not group.is_full_member(u):
                group.join(u, 'member')

    if not clean_input.get("addAllUsers"):
        url = get_base_url() + '/groups/invitations/?invitecode='

        for user_input in clean_input.get("users"):
            if 'guid' in user_input:
                try:
                    receiving_user = User.objects.get(id=user_input['guid'])
                    email = receiving_user.email
                except ObjectDoesNotExist:
                    raise GraphQLError(COULD_NOT_FIND)
            elif 'email' in user_input:
                try:
                    receiving_user = User.objects.get(email=user_input['email'])
                    email = receiving_user.email
                except Exception:
                    receiving_user = None
                    email = user_input['email']

            if clean_input.get("directAdd"):
                if not group.is_full_member(receiving_user):
                    group.join(receiving_user, 'member')
                continue

            code = None

            try:
                if receiving_user:
                    code = GroupInvitation.objects.get(invited_user=receiving_user, group=group).code
            except ObjectDoesNotExist:
                pass

            try:
                code = GroupInvitation.objects.get(email=email, group=group).code
            except ObjectDoesNotExist:
                pass

            if not code:
                code = generate_code()
                GroupInvitation.objects.create(code=code, invited_user=receiving_user, group=group, email=email)

            try:
                language = None
                if receiving_user:
                    language = receiving_user.get_language()
                    translation.activate(language)
                else:
                    translation.activate(config.LANGUAGE)

                subject = ugettext_lazy("Invitation to become a member of the %(group_name)s group") % {'group_name': group.name}
                schema_name = parse_tenant_config_path("")
                context = get_default_email_context(user)
                link = url + code
                context['link'] = link
                context['group_name'] = group.name
                send_mail_multi.delay(
                    schema_name,
                    subject,
                    'email/invite_to_group.html',
                    context,
                    email,
                    language=language
                )
            except Exception:
                # TODO: logging
                pass

    return {
        "group": group
    }
