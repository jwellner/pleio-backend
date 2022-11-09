from core.constances import INVALID_SUBTYPE, INVALID_DATE, ORDER_DIRECTION, NOT_LOGGED_IN, USER_ROLES, USER_NOT_SITE_ADMIN
from core.models import Entity, Group, SearchQueryJournal
from core.utils.elasticsearch import QueryBuilder
from user.models import User
from graphql import GraphQLError
from itertools import chain
from django.utils import dateparse, timezone


def resolve_search(_, info,
                   q=None,
                   containerGuid=None,
                   type=None,
                   subtype=None,
                   subtypes=None,
                   dateFrom=None,
                   dateTo=None,
                   offset=0,
                   limit=20,
                   tags=None,
                   tagCategories=None,
                   matchStrategy='any',
                   orderBy=None,
                   orderDirection=ORDER_DIRECTION.asc,
                   ownerGuids=None):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    total = 0
    totals = []

    request = info.context["request"]

    user = request.user
    sessionid = request.COOKIES.get('sessionid', None)

    if q:
        SearchQueryJournal.objects.maybe_log_query(
            query=q,
            session=sessionid,
        )

    q = q or '*'

    if type in ['group', 'user']:
        subtype = type

    subtypes_available = ['user', 'group', 'file', 'folder', 'pad', 'blog', 'discussion',
                        'event', 'news', 'question', 'wiki', 'page']

    if subtypes and [type for type in subtypes if type not in subtypes_available]:
        raise GraphQLError(INVALID_SUBTYPE)

    if subtype and subtype not in subtypes_available:
        raise GraphQLError(INVALID_SUBTYPE)

    # TODO: Check what happens if site alters default ACL (IE: from default "logged_in" to "public")
    # TODO: Tests
    try:
        date_from = dateparse.parse_datetime(dateFrom) if dateFrom else None
        date_to = dateparse.parse_datetime(dateTo) if dateTo else None
    except ValueError:
        raise GraphQLError(INVALID_DATE)

    query = QueryBuilder(q, user, date_from, date_to)
    query.maybe_filter_owners(ownerGuids)
    query.maybe_filter_subtypes(subtypes)
    query.maybe_filter_container(containerGuid)
    query.maybe_filter_tags(tags, matchStrategy)
    query.maybe_filter_categories(tagCategories, matchStrategy)
    query.order_by(orderBy, orderDirection)
    query.add_aggregation()

    s = query.s[offset:offset + limit]

    response = s.execute()

    # TODO: maybe response can be extended, so duplicate code can be removed
    for t in response.aggregations.type_terms.buckets:
        totals.append({"subtype": t.key, "total": t.doc_count})
        total = total + t.doc_count

    if subtype:
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
