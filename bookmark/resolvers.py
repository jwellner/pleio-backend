from ariadne import ObjectType
from bookmark.models import Bookmark
from core.constances import NOT_LOGGED_IN, COULD_NOT_FIND, INVALID_SUBTYPE
from core.lib import remove_none_from_dict
from core.models import Entity
from core.resolvers.shared import get_model_by_subtype
from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

query = ObjectType("Query")
mutation = ObjectType("Mutation")

def conditional_subtype_filter(subtype):
    if not subtype or subtype == "all":
        return Q()

    model = get_model_by_subtype(subtype)

    if model:
        filter_content_type = ContentType.objects.get_for_model(model)
        return Q(content_type=filter_content_type)
    
    raise GraphQLError(INVALID_SUBTYPE)

@query.field("bookmarks")
def resolve_bookmarks(_, info, subtype=None, tags=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # TODO: tags are not used in frontend: i would like to propose to remove them from this query.

    user = info.context.user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    qs = Bookmark.objects
    qs = qs.filter(user=user, key='bookmark')
    qs = qs.filter(conditional_subtype_filter(subtype))
    qs = qs[offset:offset+limit]

    entities = [item.content_object for item in qs]

    return {
        'total': qs.count(),
        'canWrite': False,
        'edges': entities,
    }

@mutation.field("bookmark")
def resolve_bookmark(_, info, input):
    # pylint: disable=redefined-builtin
    # TODO: what is isFirstbookmark can we delete it?

    user = info.context.user

    clean_input = remove_none_from_dict(input)

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        entity = Entity.objects.visible(user).get_subclass(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    bookmark = Bookmark.objects.get_for(user=user, content_object=entity, key='bookmark')

    if not clean_input.get("isAdding"):
        if bookmark:
            bookmark.delete()
    else:
        if not bookmark:
            Bookmark.objects.add(user=user, content_object=entity, key='bookmark')

    isFirstBookmark = False

    if clean_input.get("isAdding"):
        qs = Bookmark.objects
        qs = qs.filter(user=user, key='bookmark')
        isFirstBookmark = qs.count() == 1

    return {
        "object": entity,
        "isFirstBookmark": isFirstBookmark
    }


resolvers = [query, mutation]
