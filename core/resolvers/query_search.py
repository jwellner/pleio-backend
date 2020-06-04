from core.lib import get_acl
from core.constances import INVALID_SUBTYPE
from core.models import Entity, Group
from user.models import User
from elasticsearch_dsl import Search
from elasticsearch_dsl import A, Q
from graphql import GraphQLError
from itertools import chain
from django_tenants.utils import parse_tenant_config_path


def resolve_search(_, info, q=None, containerGuid=None, type=None, subtype=None, dateFrom="", dateTo="", offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-locals

    total = 0
    totals = []
    ids = []

    user = info.context.user
    tenant_name = parse_tenant_config_path("")

    if type in ['group', 'user']:
        subtype = type

    subtypes = ['user', 'group', 'file', 'folder', 'blog', 'discussion', 'event', 'news', 'question', 'wiki', 'page']

    if subtype and subtype not in subtypes:
        raise GraphQLError(INVALID_SUBTYPE)

    # TODO: Check what happens if site alters default ACL (IE: from default "logged_in" to "public")
    # TODO: Tests

    # search in index entities
    s = Search(index='entities').query(
            Q('multi_match', query=q, fields=['title^2', 'description', 'tags'])
        ).filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'match', tenant_name=tenant_name
        ).filter(
            'range', created_at={'gte': dateFrom, 'lte': dateTo}
        )

    a = A('terms', field='type')
    s.aggs.bucket('type_terms', a)

    s = s[offset:offset+limit]
    response = s.execute()

    # TODO: maybe response can be extended, so duplicate code can be removed
    for t in response.aggregations.type_terms.buckets:
        totals.append({"subtype": t.key, "total": t.doc_count})
        total = total + t.doc_count

    ids = []
    for hit in response:
        if subtype and subtype != hit['type']:
            continue
        ids.append(hit['id'])

    # search in index users
    s = Search(index='users').query(
            Q('multi_match', query=q, fields=['name^2', ]) |
            Q('nested', path='_profile', query=Q('bool', must=[
                    Q('match', _profile__user_profile_fields__value=q) &
                    Q('terms', _profile__user_profile_fields__read_access=list(get_acl(user)))
                    ]
                )
            )
        ).filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'match', tenant_name=tenant_name
        ).filter(
            'range', created_at={'gte': dateFrom, 'lte': dateTo}
        )

    a = A('terms', field='type')
    s.aggs.bucket('type_terms', a)

    s = s[offset:offset+limit]
    response = s.execute()

    # TODO: maybe response can be extended, so duplicate code can be removed
    for t in response.aggregations.type_terms.buckets:
        totals.append({"subtype": t.key, "total": t.doc_count})
        total = total + t.doc_count

    for hit in response:
        if subtype and subtype != hit['type']:
            continue
        ids.append(hit['id'])

    # search in index groups
    s = Search(index='groups').query(
            Q('multi_match', query=q, fields=['name^2', 'desciption', 'introduction'])
        ).filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'match', tenant_name=tenant_name
        ).filter(
            'range', created_at={'gte': dateFrom, 'lte': dateTo}
        )

    a = A('terms', field='type')
    s.aggs.bucket('type_terms', a)

    s = s[offset:offset+limit]
    response = s.execute()

    # TODO: maybe response can be extended, so duplicate code can be removed
    for t in response.aggregations.type_terms.buckets:
        totals.append({"subtype": t.key, "total": t.doc_count})
        total = total + t.doc_count

    for hit in response:
        if subtype and subtype != hit['type']:
            continue
        ids.append(hit['id'])


    # get and combine objects
    entities = Entity.objects.filter(id__in=ids).select_subclasses()
    users = User.objects.filter(id__in=ids)
    groups = Group.objects.filter(id__in=ids)
    objects = chain(entities, users, groups)

    # use elasticsearch ordering on objects
    id_dict = {str(d.id): d for d in objects}
    sorted_objects = [id_dict[id] for id in ids]

    return {
        'total': total,
        'totals': totals,
        'edges': sorted_objects
    }
