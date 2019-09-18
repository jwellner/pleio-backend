# TODO: Implement search
from core.lib import get_acl
from core.constances import INVALID_SUBTYPE
from core.models import Entity
from elasticsearch_dsl import Search
from elasticsearch_dsl import Q
from graphql import GraphQLError


def resolve_search(_, info, q=None, containerGuid=None, type=None, subtype=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    user = info.context.user

    subtypes = ['user', 'group', 'file', 'folder', 'blog', 'discussion', 'event', 'news', 'question', 'wiki', 'page']

    if subtype and subtype not in subtypes:
        raise GraphQLError(INVALID_SUBTYPE)

    s = Search().query(Q('multi_match', query=q, fields=['title^2', 'description', 
                          'tags'])).filter("terms", read_access=list(get_acl(user)))[offset:offset+limit]

    response = s.execute()

    ids = []
    for hit in response:
        ids.append(hit['id'])

    qs = Entity.objects.filter(id__in=ids).select_subclasses()
    total = qs.count()

    return {
        'total': total,
        'totals': [],
        'edges': qs
    }
