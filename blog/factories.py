from mixer.backend.django import mixer

from blog.models import Blog
from core.constances import ACCESS_TYPE
from user.models import User


def BlogFactory(**attributes) -> Blog:
    assert isinstance(attributes.get('owner'), User), "owner is a required property"
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return mixer.blend(Blog, **attributes)
