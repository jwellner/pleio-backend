from core.lib import get_acl
from core.constances import INVALID_SUBTYPE, INVALID_DATE
from core.models import Entity, Group
from user.models import User
from elasticsearch_dsl import Search
from elasticsearch_dsl import A, Q
from graphql import GraphQLError
from itertools import chain
from django_tenants.utils import parse_tenant_config_path
from django.utils import dateparse


def resolve_search(_, info, q=None, containerGuid=None, type=None, subtype=None, dateFrom=None, dateTo=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches

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
    try:
        date_from = dateparse.parse_datetime(dateFrom) if dateFrom else None
        date_to = dateparse.parse_datetime(dateTo) if dateTo else None
    except ValueError:
        raise GraphQLError(INVALID_DATE)

    s = Search(index='_all').query(
            Q('multi_match', query=q, fields=['title^2', 'name^2', 'description', 'tags', 'file_contents', 'introduction']) |
            Q('nested', path='_profile', ignore_unmapped=True, query=Q('bool', must=[
                    Q('exists', field='_profile') &
                    Q('match', _profile__user_profile_fields__value=q) &
                    Q('terms', _profile__user_profile_fields__read_access=list(get_acl(user)))
                    ]
                )
            )
        ).filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'term', tenant_name=tenant_name
        ).filter(
            'range', created_at={'gte': date_from, 'lte': date_to}
        )

    a = A('terms', field='type')
    s.aggs.bucket('type_terms', a)
    
    s = s[offset:offset+limit]
    response = s.execute()

    # TODO: maybe response can be extended, so duplicate code can be removed
    for t in response.aggregations.type_terms.buckets:
        totals.append({"subtype": t.key, "total": t.doc_count})
        total = total + t.doc_count

    if subtype and subtype in ['file', 'folder', 'blog', 'discussion', 'event', 'news', 'question', 'wiki', 'page', 'user', 'group']:
        s = s.filter('term', type=subtype)
        response = s.execute()

    ids = []
    for hit in response:
        ids.append(hit['id'])

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
