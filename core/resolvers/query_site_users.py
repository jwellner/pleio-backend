from user.models import User
from core.constances import NOT_LOGGED_IN, USER_NOT_SITE_ADMIN
from graphql import GraphQLError


def resolve_site_users(_, info, q=None, isAdmin=None, isDeleteRequested=None, isBanned=False, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments

    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.is_admin:
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    users = User.objects.all().order_by('name').exclude(name="Verwijderde gebruiker")

    if isBanned:
        users = users.filter(is_active=False)
    else:
        users = users.filter(is_active=True)

    if q:
        users = users.filter(name__icontains=q)

    if isAdmin is not None:
        users = users.filter(is_admin=isAdmin)

    if isDeleteRequested is not None:
        users = users.filter(is_delete_requested=isDeleteRequested)

    edges = users[offset:offset+limit]

    return {
        'total': users.count(),
        'edges': edges
    }
