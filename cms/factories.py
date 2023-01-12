from mixer.backend.django import mixer

from cms.models import Page
from core.constances import ACCESS_TYPE, USER_ROLES
from user.models import User


def TextPageFactory(**attributes) -> Page:
    return _common_page_factory(page_type='text', **attributes)


def CampagnePageFactory(**attributes) -> Page:
    return _common_page_factory(page_type='campagne', **attributes)


def _common_page_factory(**attributes) -> Page:
    assert isinstance(attributes.get('owner'), User), "owner is a required property"
    assert USER_ROLES.EDITOR in attributes['owner'].roles, "The owner should have the USER_ROLES.EDITOR role."
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return mixer.blend(Page, **attributes)
