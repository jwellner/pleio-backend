from ariadne import ObjectType
from event.models import Event
from django.db.models import Q
from django.utils import timezone

query = ObjectType("Query")


def early_this_morning():
    now = timezone.now()
    return timezone.datetime(year=now.year,
                             month=now.month,
                             day=now.day,
                             hour=0,
                             minute=0,
                             second=0,
                             tzinfo=now.tzinfo)


def conditional_date_filter(date_filter):
    if date_filter == 'previous':
        return Q(start_date__lt=early_this_morning())
    return Q(start_date__gte=early_this_morning())


def conditional_group_filter(container_guid):
    if container_guid == "1":
        return Q(group=None)
    if container_guid:
        return Q(group__id=container_guid)
    return Q()


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

    edges = qs[offset:offset + limit]

    return {
        'total': qs.count(),
        'edges': edges
    }
