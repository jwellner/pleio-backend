from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE, USER_ROLES
from news.models import News
from user.models import User


def NewsFactory(**attributes):
    assert isinstance(attributes.get('owner'), User), "owner is a required property"
    assert USER_ROLES.EDITOR in attributes['owner'].roles, "The owner should have the USER_ROLES.EDITOR role."
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return mixer.blend(News, **attributes)
