from core.models import Group
from core.resolvers.query_entities import conditional_tags_filter, conditional_tag_lists_filter


def resolve_groups(
        _,
        info,
        q=None,
        filter=None,
        tags=None,
        tagCategories=None,
        matchStrategy='any',
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

    if tags or tagCategories:
        groups = groups.filter(conditional_tags_filter(tags, matchStrategy == 'any') &
                               conditional_tag_lists_filter(tagCategories, matchStrategy != 'all'))

    edges = groups.order_by('-is_featured', 'name')[offset:offset + limit]

    return {
        'total': groups.count(),
        'edges': edges
    }
