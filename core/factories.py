from faker import Faker
from mixer.backend.django import mixer


def SearchQueryJournalFactory(**kwargs):
    from core.models import SearchQueryJournal
    kwargs.setdefault('query', Faker().name())
    journal = mixer.blend(SearchQueryJournal, **kwargs)

    if 'created_at' in kwargs:
        journal.created_at = kwargs['created_at']
        journal.save()
    return journal


def GroupFactory(**kwargs):
    assert kwargs.get('owner'), "Groups should have an owner"

    from core.models import Group
    group = mixer.blend(Group, **kwargs)
    group.join(kwargs['owner'], 'owner')
    return group


def AttachmentFactory(**kwargs):
    assert kwargs.get('attached'), "Attachments are required to have 'attached' filled."
    from core.models import Attachment
    return mixer.blend(Attachment, **kwargs)
