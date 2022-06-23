import re

from django.db import models
from django.db.models import Count
from django.utils import timezone


def valid_query(query):
    return re.match(r'.+', str(query).strip())


class SearchQueryJournalManager(models.Manager):

    def maybe_log_query(self, query, session):
        if valid_query(query) and (not session or not self.has_recent_duplicate(query, session)):
            return self.create(query=query, session=session)
        return None

    def has_recent_duplicate(self, query, session):
        """
        Allow register a query once per session per 10 minutes.
        """
        threshold = timezone.now() - timezone.timedelta(minutes=10)

        recent_records = self.get_queryset().filter(
            created_at__gte=threshold,
            session=session,
            query__iexact=query
        )

        return recent_records.exists()

    def last_month(self):
        return self.summary(timezone.now() - timezone.timedelta(weeks=4), timezone.now())

    def summary(self, start, end):
        items = self.get_queryset().filter(
            created_at__gt=start,
            created_at__lte=end,
        )
        return items.values('query') \
            .annotate(count=Count('query')) \
            .order_by('-count')


class SearchQueryJournal(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    query = models.CharField(max_length=255)
    session = models.CharField(max_length=255, null=True, blank=True)

    objects = SearchQueryJournalManager()

    def __str__(self):
        return self.query

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"
