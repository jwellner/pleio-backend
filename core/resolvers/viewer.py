import logging
from ariadne import ObjectType
from django.core.exceptions import ValidationError
from core.models import Entity
from core.lib import get_acl
from core.constances import ACCESS_TYPE, USER_ROLES

logger = logging.getLogger(__name__)

viewer = ObjectType("Viewer")

@viewer.field('user')
def resolve_user(_, info):
    user = info.context["request"].user

    if user.is_authenticated:
        return user
    return None

@viewer.field('canWriteToContainer')
def resolve_can_write_to_container(obj, info, containerGuid=None, subtype=None, type=None):
    # pylint: disable=unused-argument
    # pylint: disable=redefined-builtin

    user = info.context["request"].user

    # anonymous always return false
    if not user.is_authenticated:
        return False

    # check site access
    if not containerGuid and user.is_authenticated:
        if user.has_role(USER_ROLES.ADMIN):
            return True
        if subtype not in ['news', 'page']:
            return True
        if subtype in ['news', 'page'] and user.has_role(USER_ROLES.EDITOR):
            return True
        return False

    # check if containerGuid is Entity (only used for wiki / files?)
    try:
        entity = Entity.objects.filter(id=containerGuid).first()
        if entity:
            return entity.can_write(user)
    except ValidationError as e:
        logger.error("Catched error %s", e)
        return False

    # else container should be group, members can add all content to group
    if (containerGuid and ACCESS_TYPE.group.format(containerGuid) in get_acl(user)) or user.has_role(USER_ROLES.ADMIN):
        return True

    return False
