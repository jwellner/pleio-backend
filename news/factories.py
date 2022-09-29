from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from news.models import News
from user.factories import EditorFactory


def NewsFactory(**attributes):
    if 'owner' not in attributes:
        attributes['owner'] = EditorFactory()
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return mixer.blend(News, **attributes)
