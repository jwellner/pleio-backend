from ariadne import ObjectType
from core.lib import get_acl
from core.constances import ACCESS_TYPE

viewer = ObjectType("Viewer")

@viewer.field('user')
def resolve_user(_, info):
    user = info.context.user

    if user.is_authenticated:
        return user
    return None

@viewer.field('canWriteToContainer')
def resolve_can_write_to_container(obj, info, containerGuid=None, subtype=None, type=None):
    # pylint: disable=unused-argument
    # pylint: disable=redefined-builtin

    user = info.context.user

    # anonymous always return false
    if not user.is_authenticated:
        return False

    # check site access
    if not containerGuid and user.is_authenticated:
        if subtype not in ['news', 'page'] or user.is_admin:
            return True
        return False

    # check group access (is containerGuid always group?)
    if (containerGuid and ACCESS_TYPE.group.format(containerGuid) in get_acl(user)) or user.is_admin:
        return True

    return False
