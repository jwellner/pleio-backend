from django.contrib.postgres import fields
from django.core.exceptions import ValidationError

from core import config
from django.utils.translation import gettext, gettext_lazy as _

from auditlog.registry import auditlog
from django.db import models
from core.models import (ArticleMixin, AttachmentMixin, BookmarkMixin, CommentMixin, Entity, FollowMixin,
                         NotificationMixin)

from core.models.featured import FeaturedCoverMixin
from core.models.mixin import TitleMixin, RichDescriptionMediaMixin
from event.mail_builders.qr_code import submit_mail_event_qr
from event.mail_builders.waitinglist import submit_mail_at_accept_from_waitinglist
from user.models import User
from django.utils.text import slugify
from django.utils import timezone


class Event(RichDescriptionMediaMixin, TitleMixin, CommentMixin, BookmarkMixin, FollowMixin, NotificationMixin, FeaturedCoverMixin, ArticleMixin,
            AttachmentMixin, Entity):
    class Meta:
        ordering = ['-published']

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

    attendee_welcome_mail_content = models.TextField(default='', null=True, blank=True)
    attendee_welcome_mail_subject = models.CharField(max_length=256, null=True, default='', blank=True)

    def has_children(self):
        if self.children.count() > 0:
            return True
        return False

    def get_attendee(self, email):
        try:
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
            prefix, self.guid, self.slug
        ).lower()

    @property
    def rich_fields(self):
        return [self.rich_description]

    def process_waitinglist(self):
        for attendee in self.attendees.filter(state='waitinglist').order_by('updated_at'):
            if self.is_full():
                break

            attendee.update_state('accept')
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

    def save(self, *args, **kwargs):
        # When a subevent is edited and saved, the fields dependent on the parent are updated accordingly.
        self.finalize_subevent()
        self.finalize_slots_available()
        super(Event, self).save(*args, **kwargs)
        self.update_subevents()

    def update_subevents(self):
        """ Subevents are dependent on the main event, so when an event is saved, its subevents are updated """
        for child in Event.objects.filter(parent=self):
            child.is_archived = self.is_archived
            child.published = self.published
            child.read_access = self.read_access
            child.write_access = self.write_access
            child.owner = self.owner
            child.group = self.group
            child.save()


class EventAttendee(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'email'], name="unique_email"),
            models.UniqueConstraint(fields=['event', 'user'], name="unique_user")
        ]
        ordering = ('updated_at',)

    STATE_TYPES = (
        ('accept', _('Accepted')),
        ('maybe', _('Maybe')),
        ('reject', _('Rejected')),
        ('waitinglist', _('At waitinglist'))
    )

    _state_label = {key: label for key, label in STATE_TYPES}

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
                    raise ValidationError(gettext("You already signed in for another sub-event in the same slot."))

    def save(self, *args, **kwargs):
        if self.user:
            self.name = self.user.name
            self.email = self.user.email
        self.full_clean()
        super(EventAttendee, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        event = self.event
        super(EventAttendee, self).delete(*args, **kwargs)
        event.process_waitinglist()

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

    def format_state(self):
        if bool(self.checked_in_at):
            return _("Checked in")
        return self._state_label.get(self.state) or self.state

    def update_state(self, new_state):
        if new_state == self.state:
            return

        self.state = new_state

        if new_state == 'accept' and self.event.attendee_welcome_mail_content:
            from event.mail_builders.attendee_welcome_mail import send_mail
            send_mail(attendee=self)


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
