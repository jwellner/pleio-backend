from core.constances import NOT_LOGGED_IN, INVALID_SUBTYPE
from core.models import Annotation
from core.lib import get_model_by_subtype
from graphql import GraphQLError
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def conditional_subtype_filter(subtype):
    if not subtype or subtype == "all":
        return Q()

    model = get_model_by_subtype(subtype)

    if model:
        filter_content_type = ContentType.objects.get_for_model(model)
        return Q(content_type=filter_content_type)
    
    raise GraphQLError(INVALID_SUBTYPE)

def resolve_bookmarks(
        _, 
        info, 
        offset=0, 
        limit=20, 
        subtype=None
):
    # pylint: disable=unused-argument

    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    qs = Annotation.objects
    qs = qs.filter(user=user, key='bookmarked')
    qs = qs.filter(conditional_subtype_filter(subtype))
    total = qs.count()
    qs = qs[offset:offset+limit]

    entities = [item.content_object for item in qs]

    return {
        'total': total,
        'edges': entities,
    }
