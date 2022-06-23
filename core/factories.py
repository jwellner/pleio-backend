from django.utils.crypto import get_random_string
from faker import Faker
from mixer.backend.django import mixer

from core.models import SearchQueryJournal


def SearchQueryJournalFactory(**kwargs):
    kwargs.setdefault('query', Faker().name())
    journal = mixer.blend(SearchQueryJournal, **kwargs)

    if 'created_at' in kwargs:
        journal.created_at = kwargs['created_at']
        journal.save()
    return journal
