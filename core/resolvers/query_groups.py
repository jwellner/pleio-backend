from core.models import Group

def resolve_groups(
    _,
    info,
    q=None,
    filter=None,
    offset=0,
    limit=20
):
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    # pylint: disable=redefined-builtin

    user = info.context.user

    groups = Group.objects.visible(user)
    if q:
        groups = groups.filter(name__icontains=q)
    
    groups = groups[offset:offset+limit]

    return {
        'total': groups.count(),
        'canWrite': False,
        'edges': groups
    }
