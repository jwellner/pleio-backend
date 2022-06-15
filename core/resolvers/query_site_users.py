from django.utils import dateparse
from user.models import User
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN, USER_ROLES, INVALID_DATE
from graphql import GraphQLError


def resolve_site_users(_, info,
                       q=None, role=None, isDeleteRequested=None, isBanned=False, lastOnlineBefore=None, memberSince=None,
                       orderBy=None, orderDirection=None,
                       offset=0, limit=20):
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

    users = User.objects.get_filtered_users(q=q,
                                            role=role,
                                            is_delete_requested=isDeleteRequested,
                                            is_banned=isBanned,
                                            last_online_before=last_online_before,
                                            member_since=memberSince)

    users = _ordered_query(users, orderBy, orderDirection)

    edges = users[offset:offset + limit]

    return {
        'total': users.count(),
        'edges': edges
    }


def _ordered_query(qs, orderBy=None, orderDirection=None):
    if orderBy:
        order = None
        if orderBy == 'memberSince':
            order = 'created_at'

        if orderDirection.lower() == 'desc':
            order = '-%s' % order

        if order:
            return qs.order_by(order)

    return qs
