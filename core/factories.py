from faker import Faker
from mixer.backend.django import mixer

from user.models import User


def SearchQueryJournalFactory(**kwargs):
    from core.models import SearchQueryJournal
    kwargs.setdefault('query', Faker().name())
    journal = mixer.blend(SearchQueryJournal, **kwargs)

    if 'created_at' in kwargs:
        journal.created_at = kwargs['created_at']
        journal.save()
    return journal


def GroupFactory(**attributes):
    assert isinstance(attributes.get('owner'), User), "owner is a required property"

    from core.models import Group
    group = mixer.blend(Group, **attributes)
    group.join(attributes['owner'], 'owner')
    return group


def AttachmentFactory(**kwargs):
    assert kwargs.get('attached'), "Attachments are required to have 'attached' filled."
    from core.models import Attachment
    return mixer.blend(Attachment, **kwargs)
