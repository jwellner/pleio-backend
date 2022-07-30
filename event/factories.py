from django.utils.timezone import localtime
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from event.models import Event


def EventFactory(**kwargs) -> Event:
    if 'owner' not in kwargs:
        assert ('parent' in kwargs) and kwargs['parent'].owner, "Provide an owner for the event."
        kwargs['owner'] = kwargs['parent'].owner
    kwargs.setdefault('read_access', [ACCESS_TYPE.public])
    kwargs.setdefault('write_access', [ACCESS_TYPE.user.format(kwargs['owner'].guid)])
    kwargs.setdefault('start_date', localtime())
    kwargs.setdefault('end_date', kwargs['start_date'])
    return mixer.blend(Event, **kwargs)
