from django.contrib.postgres import fields
from django.core.exceptions import ValidationError

from core import config
from django.utils.translation import gettext as _

from auditlog.registry import auditlog
from django.db import models
from core.lib import get_default_email_context
from core.models import (ArticleMixin, AttachmentMixin, BookmarkMixin, CommentMixin, Entity, FollowMixin,
                         NotificationMixin)
from django_tenants.utils import parse_tenant_config_path

from core.models.featured import FeaturedCoverMixin
from event.lib import get_url
from event.mail_builders.qr_code import submit_mail_event_qr
from event.mail_builders.waitinglist import submit_mail_at_accept_from_waitinglist
from user.models import User
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone


class Event(Entity,
            CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin, FeaturedCoverMixin, ArticleMixin,
            AttachmentMixin):
    class Meta:
        ordering = ['-published']

    title = models.CharField(max_length=256)

    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)
    slots_available = models.JSONField(default=list)
    shared_via_slot = fields.ArrayField(models.CharField(max_length=40), default=list)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    location = models.CharField(max_length=256, default="")
    location_address = models.CharField(max_length=256, default="")
    location_link = models.CharField(max_length=256, default="")
    external_link = models.TextField(default="")

    ticket_link = models.TextField(blank=True, default="")

    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    rsvp = models.BooleanField(default=False)
    attend_event_without_account = models.BooleanField(default=False)

    qr_access = models.BooleanField(default=False)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def get_attendee(self, email):
        try:
            user = User.objects.filter(email=email).first()
            if user:
                return self.attendees.get(user=user)

            return self.attendees.get(email=email)
        except EventAttendee.DoesNotExist:
            pass

    def delete_attendee(self, email):
        attendee = self.get_attendee(email)
        if not attendee:
            return False
        attendee.delete()
        return True

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
        link = get_url(self)
        subject = _("Added to event %s from waitinglist") % self.title

        schema_name = parse_tenant_config_path("")
        context = get_default_email_context()
        context['link'] = link
        context['title'] = self.title

        context['location'] = self.location if self.location else None
        context['locationLink'] = self.location_link if self.location_link else None
        context['locationAddress'] = self.location_address if self.location_address else None

        context['start_date'] = self.start_date
        for attendee in self.attendees.filter(state='waitinglist').order_by('updated_at'):
            if self.is_full():
                break

            attendee.state = 'accept'
            attendee.save()

            if self.qr_access:
                submit_mail_event_qr(attendee)

            submit_mail_at_accept_from_waitinglist(event=self.guid, attendee=attendee.id)

        return True

    def get_slots(self):
        if not self.parent:
            return
        for n, slot in enumerate(self.parent.slots_available):
            if self.guid in slot.get('subEventGuids', []):
                yield {"id": n, "name": slot['name']}

    def get_slot_ids(self):
        for slot in self.get_slots():
            yield f"{slot['id']}:{slot['name']}"

    def is_in_same_slot(self, other):
        return bool([x for x in self.get_slot_ids() if x in other.get_slot_ids()])

    def finalize_subevent(self):
        if not self.parent:
            return

        self.is_archived = self.parent.is_archived
        self.published = self.parent.published
        self.read_access = self.parent.read_access
        self.write_access = self.parent.write_access
        self.owner = self.parent.owner
        self.group = self.parent.group

    def finalize_slots_available(self):
        if self.parent:
            return
        shared_slots = {}
        for slot in self.slots_available:
            if 'subEventGuids' not in slot:
                continue
            for guid in slot['subEventGuids']:
                shared_slots[guid] = []
                for shared_with in slot['subEventGuids']:
                    shared_slots[guid].append(shared_with)

        # Reset previous setting
        Event.objects.filter(parent=self).update(shared_via_slot=[])

        # Apply new setting
        for guid, shared_via_slot in shared_slots.items():
            Event.objects.filter(id=guid).update(shared_via_slot=shared_via_slot)


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
        null=True, blank=True,
        max_length=16,
        choices=STATE_TYPES,
    )

    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.EmailField(max_length=256, null=False, blank=False)
    code = models.CharField(max_length=36, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    checked_in_at = models.DateTimeField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    @property
    def user_icon(self):
        return self.user.icon if self.user else None

    @property
    def user_url(self):
        return self.user.url if self.user else None

    @property
    def language(self):
        if self.user:
            return self.user.get_language()
        return config.LANGUAGE

    def __str__(self):
        return f"EventAttendee[{self.name}]"

    def clean(self):
        self.clean_event()

    def clean_event(self):
        if not self.event.parent or self.state != 'accept' \
                or self.event.start_date is None \
                or not self.event.get_slots():
            return

        user_attendees = EventAttendee.objects.filter(user__isnull=False, user=self.user)
        email_attendees = EventAttendee.objects.filter(email__isnull=False, email=self.email)
        for qs in [user_attendees, email_attendees]:
            qs = qs.exclude(id=self.id)
            qs = qs.filter(event__parent=self.event.parent, state='accept')
            for maybe_match in qs:
                if self.event.is_in_same_slot(maybe_match.event):
                    raise ValidationError(_("You already signed in for another sub-event in the same slot."))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super(EventAttendee, self).save(force_insert, force_update, using, update_fields)

    def as_attendee(self, access_user):
        return {
            "guid": self.user.id if self.user else '',
            "email": self.email if self.event.can_write(access_user) else '',
            "name": self.name,
            "state": self.state,
            "icon": self.user_icon,
            "url": self.user_url,
            "timeCheckedIn": self.checked_in_at
        }

    def as_mailinfo(self):
        return {'name': self.name,
                'email': self.email,
                'language': self.language}


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


# Subevents are dependent on the main event, so when an event is saved, its subevents are updated.
@receiver(post_save, sender=Event)
def event_post_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument

    for child in Event.objects.filter(parent=instance):
        child.is_archived = instance.is_archived
        child.published = instance.published
        child.read_access = instance.read_access
        child.write_access = instance.write_access
        child.owner = instance.owner
        child.group = instance.group
        child.save()


# When a subevent is edited and saved, the fields dependent on the parent are updated accordingly.
@receiver(pre_save, sender=Event)
def event_pre_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    instance.finalize_subevent()
    instance.finalize_slots_available()


# When a subevent is edited and saved, the fields dependent on the parent are updated accordingly
@receiver(pre_save, sender=EventAttendee)
def event_attendee_pre_save(sender, instance, **kwargs):
    # pylint: disable=unused-argument

    if instance.user:
        instance.name = instance.user.name
        instance.email = instance.user.email


auditlog.register(Event)
auditlog.register(EventAttendee)
auditlog.register(EventAttendeeRequest)
