from mixer.backend.django import mixer

from cms.models import Page
from core.constances import ACCESS_TYPE
from user.factories import EditorFactory


def TextPageFactory(**attributes):
    return _common_page_factory(page_type='text', **attributes)


def CampagnePageFactory(**attributes):
    return _common_page_factory(page_type='campagne', **attributes)


def _common_page_factory(**attributes):
    if 'owner' not in attributes:
        attributes['owner'] = EditorFactory()
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return mixer.blend(Page, **attributes)
