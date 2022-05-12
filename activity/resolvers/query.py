from ariadne import ObjectType
from core.models import Entity
from django.db.models import Q
from core.constances import ORDER_BY, ORDER_DIRECTION

query = ObjectType("Query")


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

def conditional_tags_filter(tags):
    if tags:
        filters = Q()
        for tag in tags:
            filters.add(Q(tags__icontains=tag), Q.AND)  # of Q.OR
        return filters
    return Q()

def conditional_tag_lists_filter(tag_lists):
    filters = Q()
    if tag_lists:
        for tags in tag_lists:
            if tags:
                filters.add(Q(tags__overlap=tags), Q.AND)  # of Q.OR
    return filters

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

@query.field("activities")
def resolve_activities(
        _,
        info,
        containerGuid=None,
        offset=0,
        limit=20,
        tags=None,
        tagLists=None,
        groupFilter=None,
        subtypes=None,
        orderBy=ORDER_BY.timePublished,
        orderDirection=ORDER_DIRECTION.desc,
        sortPinned=False,
        isDraft=False,
        userGuid=None
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals

    if orderBy == ORDER_BY.timeUpdated:
        order_by = 'updated_at'
    elif orderBy == ORDER_BY.timeCreated:
        order_by = 'created_at'
    elif orderBy == ORDER_BY.lastAction:
        order_by = 'last_action'
    elif orderBy == ORDER_BY.title:
        order_by = 'title'
    else:
        order_by = 'published'

    if orderDirection == ORDER_DIRECTION.desc:
        order_by = '-%s' % (order_by)

    order = [order_by]

    if sortPinned:
        order = ["-is_pinned"] + order

    if isDraft:
        qs = Entity.objects.draft(info.context["request"].user)
    else:
        qs = Entity.objects.visible(info.context["request"].user)

    qs = qs.filter(conditional_subtypes_filter(subtypes) &
                   conditional_tags_filter(tags) &
                   conditional_tag_lists_filter(tagLists) &
                   conditional_group_filter(containerGuid) &
                   conditional_groups_filter(groupFilter, info.context["request"].user))

    if userGuid:
        qs = qs.filter(owner__id=userGuid)

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
