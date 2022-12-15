from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from question.models import Question
from user.models import User


def QuestionFactory(**attributes):
    assert isinstance(attributes.get('owner'), User), "owner is a required property"
    attributes.setdefault('read_access', [ACCESS_TYPE.public])
    attributes.setdefault('write_access', [ACCESS_TYPE.user.format(attributes['owner'].guid)])
    return mixer.blend(Question, **attributes)
