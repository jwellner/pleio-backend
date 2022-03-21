from auditlog.registry import auditlog
from django.db import models
from django_tenants.utils import parse_tenant_config_path
from django.utils.translation import ugettext_lazy
from core.lib import get_default_email_context
from core.models import Entity, CommentMixin, BookmarkMixin, NotificationMixin, FollowMixin, FeaturedCoverMixin, ArticleMixin, AttachmentMixin
from core.tasks import send_mail_multi
from event.lib import get_url
from user.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone

class Event(Entity, CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin, FeaturedCoverMixin, ArticleMixin, AttachmentMixin):
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    location = models.CharField(max_length=256, default="")
    external_link = models.TextField(default="")

    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    rsvp = models.BooleanField(default=False)
    attend_event_without_account = models.BooleanField(default=False)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def get_attendee(self, user, email=None):
        if not user.is_authenticated:
            return None

        attendee = None
        
        try:
            attendee_user = User.objects.get(email=email)
            attendee = self.attendees.get(user=attendee_user)
        except ObjectDoesNotExist:
            pass
        
        try:
            attendee = self.attendees.get(email=email)
        except ObjectDoesNotExist:
            pass

        return attendee

    def delete_attendee(self, user, email):
        deleted = False        
        if not user.is_authenticated:
            return None
        
        # try delete attendee with account
        try:
            attendee = User.objects.get(email=email)
            self.attendees.get(user=attendee).delete()
            deleted = True
        except ObjectDoesNotExist:
            pass

        # try delete attendee without account
        try:
            attendee = self.attendees.get(email=email)
            attendee.delete()
            deleted = True
        except ObjectDoesNotExist:
            pass

        # try delete attendee without account request
        try:
            EventAttendeeRequest.objects.get(event=self, email=email).delete()
        except ObjectDoesNotExist:
            pass

        return deleted

    def is_full(self):
        if self.max_attendees and self.attendees.filter(state="accept").count() >= self.max_attendees:
            return True
        return False

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

    @property
    def rich_fields(self):
        return [self.rich_description]

    def process_waitinglist(self):
        link = get_url(self, None)
        subject = ugettext_lazy("Added to event %s from waitinglist") % self.title

        schema_name = parse_tenant_config_path("")
        context = get_default_email_context()
        context['link'] = link
        context['title'] = self.title
        context['location'] = self.location
        context['start_date'] = self.start_date
        for attendee in self.attendees.filter(state='waitinglist').order_by('updated_at'):
            if self.is_full():
                break
            attendee.state = 'accept'
            attendee.save()
            try:
                send_mail_multi.delay(schema_name, subject, 'email/attend_event_from_waitinglist.html', context, attendee.user.email)
            except Exception:
                send_mail_multi.delay(schema_name, subject, 'email/attend_event_from_waitinglist.html', context, attendee.email)

        return True


class EventAttendee(models.Model):

    STATE_TYPES = (
        ('accept', 'Accept'),
        ('maybe', 'Maybe'),
        ('reject', 'Reject'),
        ('waitinglist', 'Waitinglist')
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

    checked_in_at = models.DateTimeField(default=None, null=True)
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

#Subevents are dependent on the main event, so when an event is saved, its subevents are updated
@receiver(post_save, sender=Event)
def event_post_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument

    if instance.has_children():
        for child in instance.children.all():
            child.is_archived = instance.is_archived
            child.published = instance.published
            child.read_access = instance.read_access
            child.write_access = instance.write_access
            child.owner = instance.owner
            child.group = instance.group
            child.save()

#When a subevent is edited and saved, the fields dependent on the parent are updated accordingly
@receiver(pre_save, sender=Event)
def event_pre_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    
    if instance.parent:
        instance.is_archived = instance.parent.is_archived
        instance.published = instance.parent.published
        instance.read_access = instance.parent.read_access
        instance.write_access = instance.parent.write_access
        instance.owner = instance.parent.owner
        instance.group = instance.parent.group


auditlog.register(Event)
auditlog.register(EventAttendee)
auditlog.register(EventAttendeeRequest)