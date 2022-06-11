from mixer.backend.django import mixer

from core.constances import USER_ROLES
from user.models import User


def UserFactory(**kwargs):
    return mixer.blend(User, **kwargs)


def AdminFactory(**kwargs):
    kwargs.setdefault('roles', [USER_ROLES.ADMIN])
    assert USER_ROLES.ADMIN in kwargs['roles'], "Administrators have the USER_ROLES.ADMIN role."
    return UserFactory(**kwargs)


def EditorFactory(**kwargs):
    kwargs.setdefault('roles', [USER_ROLES.EDITOR])
    assert USER_ROLES.EDITOR in kwargs['roles'], "Editors have the USER_ROLES.EDITOR role."
    return UserFactory(**kwargs)


def QuestionManagerFactory(**kwargs):
    kwargs.setdefault('roles', [USER_ROLES.QUESTION_MANAGER])
    assert USER_ROLES.QUESTION_MANAGER in kwargs['roles'], "Editors have the USER_ROLES.QUESTION_MANAGER role."
    return UserFactory(**kwargs)