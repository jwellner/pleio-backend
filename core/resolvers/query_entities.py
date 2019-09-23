from django.db.models import Q
from core.constances import ORDER_DIRECTION, ORDER_BY, INVALID_SUBTYPE
from core.models import Entity
from core.resolvers.shared import get_model_by_subtype
from graphql import GraphQLError

def conditional_group_filter(container_guid):
    """
    Filter only items in group 
    """
    if container_guid:
        return Q(group__id=container_guid)

    return Q()

def conditional_is_featured_filter(subtype, is_featured):
    """
    Only filter is_featured on news list
    """
    if subtype == "news" and is_featured:
        return Q(is_featured=is_featured)

    return Q()

def resolve_entities(
    _,
    info,
    offset=0,
    limit=20,
    type=None,
    subtype=None,
    subtypes=None,
    containerGuid=None,
    tags=None,
    orderBy=ORDER_BY.timeCreated,
    orderDirection=ORDER_DIRECTION.desc,
    addFeatured=False,
    isFeatured=False
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    if not subtype:
        Model = Entity
    elif subtype in ["news", "poll", "discussion", "event", "wiki", "question", "page", "blog"]:
        Model = get_model_by_subtype(subtype)
    else:
        raise GraphQLError(INVALID_SUBTYPE)

    if orderBy == ORDER_BY.timeUpdated:
        order_by = 'updated_at'
    elif orderBy == ORDER_BY.lastAction:
        order_by = 'updated_at'
    else:
        order_by = 'created_at'
    
    if orderDirection == ORDER_DIRECTION.desc:
        order_by = '-%s' % (order_by)

    entities = Model.objects.visible(info.context.user)
    entities = entities.filter(conditional_group_filter(containerGuid) & conditional_is_featured_filter(subtype, isFeatured))
    entities = entities.order_by(order_by)
    entities = entities[offset:offset+limit]

    return {
        'total': entities.count(),
        'canWrite': False,
        'edges': entities,
    }
