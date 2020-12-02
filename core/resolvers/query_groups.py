from core.models import Group
from django.db.models import Q


def conditional_tags_filter(tags):
    if tags:
        filters = Q()
        for tag in tags:
            filters.add(Q(tags__icontains=tag), Q.AND) # of Q.OR

        return filters
    return Q()


def resolve_groups(
    _,
    info,
    q=None,
    filter=None,
    tags=None,
    offset=0,
    limit=20
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    groups = Group.objects.visible(user)
    if q:
        groups = groups.filter(name__icontains=q)

    if filter == 'mine':
        group_ids = user.memberships.filter(type__in=('member', 'admin', 'owner')).values_list('group', flat=True)
        groups = groups.filter(id__in=group_ids)

    if tags:
        groups = groups.filter(conditional_tags_filter(tags))

    edges = groups.order_by('-is_featured', 'name')[offset:offset+limit]

    return {
        'total': groups.count(),
        'edges': edges
    }
