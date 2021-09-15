from auditlog.registry import auditlog
from django.db import models
from core.models import Entity, CommentMixin, BookmarkMixin, NotificationMixin, FollowMixin, FeaturedCoverMixin
from user.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from django.utils import timezone

class Event(Entity, CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin, FeaturedCoverMixin):
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)
    description = models.TextField()
    rich_description = models.TextField(null=True, blank=True)

    is_featured = models.BooleanField(default=False)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    location = models.CharField(max_length=256, default="")
    external_link = models.TextField(default="")

    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    rsvp = models.BooleanField(default=False)
    attend_event_without_account = models.BooleanField(default=False)

    def get_attendee(self, user):
        if not user.is_authenticated:
            return None

        try:
            attendee = self.attendees.get(user=user)
        except ObjectDoesNotExist:
            return None

        return attendee

    def __str__(self):
        return f"Event[{self.title}]"

    @property
    def type_to_string(self):
        return 'event'

    @property
    def url(self):
        prefix = ''

        if self.group:
            prefix = '/groups/view/{}/{}'.format(
                self.group.guid, slugify(self.group.name)
            )

        return '{}/events/view/{}/{}'.format(
            prefix, self.guid, slugify(self.title)
        ).lower()


class EventAttendee(models.Model):

    STATE_TYPES = (
        ('accept', 'Accept'),
        ('maybe', 'Maybe'),
        ('reject', 'Reject')
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='attendees'
    )

    state = models.CharField(
        max_length=16,
        choices=STATE_TYPES
    )

    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.CharField(max_length=256, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"EventAttendee[{self.name}]"

class EventAttendeeRequest(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=256)
    email = models.CharField(max_length=256)
    code = models.CharField(max_length=36)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"EventAttendeeRequest[{self.name}]"


auditlog.register(Event)
auditlog.register(EventAttendee)
auditlog.register(EventAttendeeRequest)