from faker import Faker
from mixer.backend.django import mixer

from core.models import Group
from user.models import User


def SearchQueryJournalFactory(**kwargs):
    from core.models import SearchQueryJournal
    kwargs.setdefault('query', Faker().name())
    journal = mixer.blend(SearchQueryJournal, **kwargs)

    if 'created_at' in kwargs:
        journal.created_at = kwargs['created_at']
        journal.save()
    return journal


def GroupFactory(**attributes) -> Group:
    assert isinstance(attributes.get('owner'), User), "Groups should have an owner"

    group = mixer.blend(Group, **attributes)
    group.join(attributes['owner'], 'owner')
    return group
