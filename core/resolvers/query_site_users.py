from django.db.models import Q
from django.utils import dateparse
from user.models import User
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, INVALID_DATE
from graphql import GraphQLError

def resolve_site_users(_, info, q=None, role=None, isDeleteRequested=None, isBanned=False, offset=0, limit=20, lastOnlineBefore=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments

    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    last_online_before = None
    if lastOnlineBefore:
        try:
            last_online_before = dateparse.parse_datetime(lastOnlineBefore)
        except ValueError:
            raise GraphQLError(INVALID_DATE)

    users = User.objects.all().order_by('name').exclude(name="Verwijderde gebruiker")

    if isBanned:
        users = users.filter(is_active=False)
    else:
        users = users.filter(is_active=True)

    if q:
        users = users.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(id__iexact=q)
        )

    if last_online_before:
        users = users.filter(_profile__last_online__lt=last_online_before)

    if role is not None and hasattr(USER_ROLES, role.upper()):
        ROLE_FILTER = getattr(USER_ROLES, role.upper())
        users = users.filter(roles__contains=[ROLE_FILTER])

    if isDeleteRequested is not None:
        users = users.filter(is_delete_requested=isDeleteRequested)

    edges = users[offset:offset+limit]

    return {
        'total': users.count(),
        'edges': edges
    }
