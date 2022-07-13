from core.lib import get_acl
from core.constances import INVALID_SUBTYPE, INVALID_DATE, ORDER_DIRECTION, SEARCH_ORDER_BY, NOT_LOGGED_IN, USER_ROLES, USER_NOT_SITE_ADMIN
from core.models import Entity, Group, SearchQueryJournal
from user.models import User
from elasticsearch_dsl import Search
from elasticsearch_dsl import A, Q
from graphql import GraphQLError
from itertools import chain
from django_tenants.utils import parse_tenant_config_path
from django.utils import dateparse, timezone


def resolve_search(_, info, q=None, containerGuid=None, type=None, subtype=None, dateFrom=None, dateTo=None, offset=0, limit=20,
                   tagLists=None, orderBy=None, orderDirection=ORDER_DIRECTION.asc):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    total = 0
    totals = []

    request = info.context["request"]

    user = request.user
    tenant_name = parse_tenant_config_path("")
    sessionid = request.COOKIES.get('sessionid', None)

    SearchQueryJournal.objects.maybe_log_query(
        query=q,
        session=sessionid,
    )

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

    if (tagLists or dateFrom or dateTo) and not q:
        q = '*'

    s = Search(index='_all').query(
        Q('simple_query_string', query=q, fields=[
            'title^3',
            'name^3',
            'email',
            'description',
            'tags^3',
            'tags_matches',
            'file_contents',
            'introduction',
            'comments.description',
            'owner.name'
        ]
          )
        | Q('nested', path='user_profile_fields', ignore_unmapped=True, query=Q('bool', must=[
            Q('match', user_profile_fields__value=q),
            Q('terms', user_profile_fields__read_access=list(get_acl(user)))
        ]
                                                                                )
            )
    ).filter(
        'terms', read_access=list(get_acl(user))
    ).filter(
        'term', tenant_name=tenant_name
    ).filter(
        'range', created_at={'gte': date_from, 'lte': date_to}
    ).exclude(
        'term', is_active=False
    )

    s = s.query('bool', filter=[
        Q('range', published={'gt': None, 'lte': timezone.now()}) |
        Q('terms', type=['group', 'user'])
    ])

    # Filter on container_guid (group.guid)
    if containerGuid:
        s = s.filter('term', container_guid=containerGuid)

    if tagLists:
        for tags in tagLists:
            s = s.filter(
                'terms', tags__raw=[x.lower() for x in tags]
            )

    if orderBy == SEARCH_ORDER_BY.title:
        s = s.sort({'title.raw': {'order': orderDirection}})
    elif orderBy == SEARCH_ORDER_BY.timeCreated:
        s = s.sort({'created_at': {'order': orderDirection}})
    elif orderBy == SEARCH_ORDER_BY.timePublished:
        s = s.sort({'published': {'order': orderDirection}})

    a = A('terms', field='type')
    s.aggs.bucket('type_terms', a)

    s = s[offset:offset + limit]
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


def resolve_search_journal(_, info, dateTimeFrom=None, dateTimeTo=None, limit=None, offset=None):
    user = info.context["request"].user

    if not user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    if not user.has_role(USER_ROLES.ADMIN):
        raise GraphQLError(USER_NOT_SITE_ADMIN)

    if dateTimeTo is None:
        dateTimeTo = timezone.now()

    if dateTimeFrom is None:
        dateTimeFrom = dateTimeTo - timezone.timedelta(weeks=4)

    if dateTimeFrom > dateTimeTo:
        raise GraphQLError(INVALID_DATE)

    summary = [s for s in SearchQueryJournal.objects.summary(
        start=dateTimeFrom,
        end=dateTimeTo,
    )]
    total = len(summary)
    if offset is not None:
        summary = summary[offset:]
    if limit is not None:
        summary = summary[:limit]
    return {
        "total": total,
        "edges": summary,
    }
