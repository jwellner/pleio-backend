from mixer.backend.django import mixer

from blog.models import Blog
from core.constances import ACCESS_TYPE
from user.factories import UserFactory


def BlogFactory(**attributes) -> Blog:
    if 'owner' not in attributes:
        attributes['owner'] = UserFactory()
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return mixer.blend(Blog, **attributes)
