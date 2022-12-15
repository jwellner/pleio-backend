from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from user.models import User
from wiki.models import Wiki


def WikiFactory(**attributes):
    assert isinstance(attributes.get('owner'), User), "owner is a required property"
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return mixer.blend(Wiki, **attributes)
