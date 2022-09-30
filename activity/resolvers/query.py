import logging

from ariadne import ObjectType
from graphql import GraphQLError
from core.lib import early_this_morning
from core.models import Entity
from django.db.models import Q
from django.db.models.functions import Coalesce
from core.constances import ORDER_BY, ORDER_DIRECTION, COULD_NOT_ORDER_BY_START_DATE, COULD_NOT_USE_EVENT_FILTER
from core.resolvers.query_entities import conditional_tags_filter, conditional_tag_lists_filter

query = ObjectType("Query")

logger = logging.getLogger(__name__)


def conditional_subtypes_filter(subtypes):
    q_objects = Q()

    if subtypes:
        for object_type in subtypes:
            if object_type == 'news':
                q_objects.add(~Q(news__isnull=True), Q.OR)
            elif object_type == 'blog':
                q_objects.add(~Q(blog__isnull=True), Q.OR)
            elif object_type == 'event':
                q_objects.add(~Q(event__isnull=True) & ~Q(event__parent__isnull=False), Q.OR)
            elif object_type == 'discussion':
                q_objects.add(~Q(discussion__isnull=True), Q.OR)
            elif object_type == 'statusupdate':
                q_objects.add(~Q(statusupdate__isnull=True), Q.OR)
            elif object_type == 'question':
                q_objects.add(~Q(question__isnull=True), Q.OR)
            elif object_type == 'wiki':
                q_objects.add(~Q(wiki__isnull=True), Q.OR)
            elif object_type == 'page':
                q_objects.add(~Q(page__isnull=True) & ~Q(page__page_type='campagne'), Q.OR)
    else:
        # activities should only search for these entities:
        q_objects.add(~Q(news__isnull=True), Q.OR)
        q_objects.add(~Q(blog__isnull=True), Q.OR)
        q_objects.add(~Q(event__isnull=True) & ~Q(event__parent__isnull=False), Q.OR)
        q_objects.add(~Q(discussion__isnull=True), Q.OR)
        q_objects.add(~Q(statusupdate__isnull=True), Q.OR)
        q_objects.add(~Q(question__isnull=True), Q.OR)
        q_objects.add(~Q(wiki__isnull=True), Q.OR)
        q_objects.add(~Q(page__isnull=True) & ~Q(page__page_type='campagne'), Q.OR)


    return q_objects

def conditional_group_filter(container_guid):
    """ Filter on one group """
    if container_guid:
        return Q(group__id=container_guid)

    return Q()


def conditional_groups_filter(group_filter, user):
    """ Filter on all or mine groups """
    if group_filter == ["all"]:
        return Q(group__isnull=False)
    if group_filter == ["mine"]:
        groups = []
        for membership in user.memberships.filter(type__in=['admin', 'owner', 'member']):
            groups.append(membership.group.id)
        return Q(group__in=groups)

    return Q()


def conditional_event_filter(date_filter):
    if date_filter == 'previous':
        return Q(event__start_date__lt=early_this_morning())
    return Q(event__start_date__gte=early_this_morning())


@query.field("activities")
def resolve_activities(
        _,
        info,
        containerGuid=None,
        offset=0,
        limit=20,
        tags=None,
        tagLists=None,
        matchStrategy='legacy',
        groupFilter=None,
        eventFilter=None,
        subtypes=None,
        orderBy=ORDER_BY.timePublished,
        orderDirection=ORDER_DIRECTION.desc,
        sortPinned=False,
        statusPublished=None,
        userGuid=None
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches

    if orderBy == ORDER_BY.timeUpdated:
        order_by = 'updated_at'
    elif orderBy == ORDER_BY.timeCreated:
        order_by = 'created_at'
    elif orderBy == ORDER_BY.lastAction:
        order_by = 'last_action'
    elif orderBy == ORDER_BY.title:
        order_by = 'title'
    elif orderBy == ORDER_BY.startDate:
        if subtypes == ['event']:
            order_by = 'event__start_date'
        else:
            raise GraphQLError(COULD_NOT_ORDER_BY_START_DATE)
    else:
        order_by = 'published'

    if orderDirection == ORDER_DIRECTION.desc:
        order_by = '-%s' % (order_by)

    title_order_by = Coalesce(
        'news__title', 
        'blog__title',
        'filefolder__title',
        'poll__title',
        'statusupdate__title',
        'wiki__title',
        'page__title', 
        'question__title', 
        'discussion__title', 
        'event__title'
    )
    if order_by == '-title':
        order_by = title_order_by.desc()
    elif order_by == 'title':
        order_by = title_order_by.asc()

    order = [order_by]

    if sortPinned:
        order = ["-is_pinned"] + order

    if (statusPublished is not None) and (len(statusPublished) > 0):
        qs = Entity.objects.status_published(statusPublished, info.context["request"].user)
    else:
        qs = Entity.objects.visible(info.context["request"].user)

    qs = qs.filter(conditional_subtypes_filter(subtypes) &
                   conditional_tags_filter(tags, matchStrategy == 'any') &
                   conditional_tag_lists_filter(tagLists, matchStrategy != 'all') &
                   conditional_group_filter(containerGuid) &
                   conditional_groups_filter(groupFilter, info.context["request"].user))

    if userGuid:
        qs = qs.filter(owner__id=userGuid)

    if eventFilter:
        if subtypes == ['event']:
            qs = qs.filter(conditional_event_filter(eventFilter))
        else:
            raise GraphQLError(COULD_NOT_USE_EVENT_FILTER)

    qs = qs.order_by(*order).select_subclasses()

    total = qs.count()

    qs = qs[offset:offset + limit]

    activities = []

    for item in qs:
        activity = {
            'guid': 'activity:%s' % (item.guid),
            'type': 'create',
            'entity': item
        }

        activities.append(activity)

    return {
        'total': total,
        'edges': activities
    }
