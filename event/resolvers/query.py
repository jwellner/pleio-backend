from copy import deepcopy

from ariadne import ObjectType
from core.lib import early_this_morning
from event.lib import complement_expected_range
from event.models import Event
from django.db.models import Q

query = ObjectType("Query")


def conditional_group_filter(container_guid):
    if container_guid == "1":
        return Q(group=None)
    if container_guid:
        return Q(group__id=container_guid)
    return Q()


def conditional_date_filter(date_filter):
    if date_filter == 'previous':
        return Q(end_date__lt=early_this_morning())
    return Q(end_date__gte=early_this_morning())


@query.field("events")
def resolve_events(obj, info, filter=None, containerGuid=None, offset=0, limit=20):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    qs = Event.objects.visible(info.context["request"].user)

    qs = qs.filter(
        conditional_date_filter(filter) &
        conditional_group_filter(containerGuid) &
        ~Q(parent__isnull=False)
    )

    if filter == 'previous':
        qs = qs.order_by('-start_date', 'title')
    else:
        qs = qs.order_by('start_date', 'title')

    complement_expected_range(deepcopy(qs),
                              offset=offset, limit=limit)
    edges = qs[offset:offset + limit]

    return {
        'total': qs.count(),
        'edges': edges
    }
