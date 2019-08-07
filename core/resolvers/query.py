from ariadne import ObjectType
from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError
from core.lib import get_type, get_id
from core.models import User
from .query_viewer import resolve_viewer
from .query_site import resolve_site
from .query_entities import resolve_entities
from .query_groups import resolve_groups
from core.constances import INVALID_SUBTYPE, COULD_NOT_FIND
from core.resolvers.shared import get_model_by_subtype

query = ObjectType("Query")

query.set_field("viewer", resolve_viewer)
query.set_field("site", resolve_site)
query.set_field("entities", resolve_entities)
query.set_field("groups", resolve_groups)

@query.field("entity")
def resolve_entity(
    _,
    info,
    guid=None,
    username=None
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    user = info.context.user

    if guid:
        subtype = get_type(guid)
        entity_id = get_id(guid)
    else:
        subtype = get_type(username)
        entity_id = get_id(username)

    model = get_model_by_subtype(subtype)

    if not model:
        raise GraphQLError(INVALID_SUBTYPE)

    try:
        entity = model.objects.visible(user).get(id=entity_id)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    return entity


# TODO: Implement search
@query.field("search")
def resolve_search(_, info, q=None, containerGuid=None, type=None, subtype=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    return {
        'total': 0,
        'totals': [],
        'edges': []
    }

# TODO: Implement recommended


@query.field("recommended")
def resolve_recommended(_, info, offset=0, limit=20):
    # pylint: disable=unused-argument
    return {
        'total': 0,
        'canWrite': False,
        'edges': []
    }

# TODO: Implement trending


@query.field("trending")
def resolve_trending(_, info):
    # pylint: disable=unused-argument
    return [
        {'tag': 'pleio', 'likes': 10},
        {'tag': 'backend2', 'likes': 3}
    ]

# TODO: Implement top


@query.field("top")
def resolve_top(_, info):
    # pylint: disable=unused-argument
    user = info.context.user

    if user.is_authenticated:
        return [
            {'user': user, 'likes': 42}
        ]

    return []

# TODO: Implement breadcrumb


@query.field("breadcrumb")
def resolve_breadcrumb(_, info, guid=None):
    # pylint: disable=unused-argument
    return []

@query.field('users')
def resolve_users(_, info, q=None, filters=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    user = info.context.user

    if not user.is_authenticated:
        return None

    users = []

    if q:
        users = User.objects.filter(name__icontains=q)[offset:offset+limit]
    else:
        users = User.objects.all()[offset:offset+limit]

    return {
        'total': users.count(),
        'edges': users,
        'filterCount': None
    }


@query.field('filters')
def resolve_filters(_, info):
    # pylint: disable=unused-argument
    return {
        'users': None
    }
