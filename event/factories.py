from django.utils.timezone import localtime
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from event.models import Event


def EventFactory(owner, **kwargs):
    kwargs.setdefault('owner', owner)
    kwargs.setdefault('read_access', [ACCESS_TYPE.public])
    kwargs.setdefault('write_access', [ACCESS_TYPE.user.format(kwargs['owner'].guid)])
    kwargs.setdefault('start_date', localtime())
    kwargs.setdefault('end_date', localtime())
    return mixer.blend(Event, **kwargs)
