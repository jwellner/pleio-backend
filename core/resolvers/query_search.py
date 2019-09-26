# TODO: Implement search
from core.lib import get_acl
from core.constances import INVALID_SUBTYPE
from core.models import Entity, User
from elasticsearch_dsl import Search
from elasticsearch_dsl import A, Q
from graphql import GraphQLError
from itertools import chain


def resolve_search(_, info, q=None, containerGuid=None, type=None, subtype=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-locals

    user = info.context.user

    subtypes = ['user', 'group', 'file', 'folder', 'blog', 'discussion', 'event', 'news', 'question', 'wiki', 'page']

    if subtype and subtype not in subtypes:
        raise GraphQLError(INVALID_SUBTYPE)

    # TODO: Users not found because of ACL, users do not have read_access field
    # TODO: Check what happens if site alters default ACL (IE: from default "logged_in" to "public")
    s = Search().query(Q('multi_match', query=q, fields=['title^2', 'description', 'name', 'email'
                         'tags'])).filter('terms', read_access=list(get_acl(user)))

    if subtype:
        s = s.filter('terms', type=[subtype])

    a = A('terms', field='type')
    s.aggs.bucket('type_terms', a)

    s = s[offset:offset+limit]
    response = s.execute()

    total = 0
    totals = []
    for t in response.aggregations.type_terms.buckets:
        totals.append({"subtype": t.key, "total": t.doc_count})
        total = total + t.doc_count

    ids = []
    for hit in response:
        ids.append(hit['id'])

    # get and combine objects
    entities = Entity.objects.filter(id__in=ids).select_subclasses()
    users = User.objects.filter(id__in=ids)
    objects = chain(entities, users)

    # use elasticsearch ordering on objects
    id_dict = {str(d.id): d for d in objects}
    sorted_objects = [id_dict[id] for id in ids]

    return {
        'total': total,
        'totals': totals,
        'edges': sorted_objects
    }
