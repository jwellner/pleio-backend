from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from poll.models import Poll


def PollFactory(**kwargs):
    assert kwargs.get('owner'), "Poll requires owner field to be set."
    kwargs.setdefault('read_access', [ACCESS_TYPE.public])
    kwargs.setdefault('write_access', [ACCESS_TYPE.user.format(kwargs['owner'].guid)])
    return mixer.blend(Poll, **kwargs)
