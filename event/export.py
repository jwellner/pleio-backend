from django.db.models import Q
from django.utils.translation import gettext as _

from core import config
from core.lib import datetime_format
from core.models import ProfileField
from event.models import EventAttendee


class AttendeeExporter:
    EXPORT_STATES = ['accept', 'waitinglist', 'maybe', 'reject']

    def __init__(self, event, acting_user):
        self.event = event
        self.children = [*self.event.children.filter(rsvp=True).order_by('start_date', 'title').values_list('pk', 'title')]
        self.acting_user = acting_user
        self.profile_fields = self.get_profile_fields()

    def rows(self):
        yield from self.export_main_event()
        yield from self.export_subevents()
        yield from self.maybe_subevent_supplement()

    def export_main_event(self):
        yield [self.event.title, datetime_format(self.event.start_date)]
        yield self.column_headers()
        for state in self.EXPORT_STATES:
            for attendee in self.event.attendees.filter(state=state):
                yield self.attendee_row(attendee)

    def export_subevents(self):
        for child in self.event.children.order_by("start_date"):
            yield []
            yield [child.title, datetime_format(child.start_date)]
            yield self.column_headers()
            for state in self.EXPORT_STATES:
                for attendee in child.attendees.filter(state=state):
                    yield self.attendee_row(attendee)

    def maybe_subevent_supplement(self):
        if not self.event.children.count():
            return

        yield []
        yield [_("All attendees")]

        qs = EventAttendee.objects.filter(Q(event=self.event) | Q(event__parent=self.event))
        processed = []

        yield [*self.column_headers(), _("All events")]
        for state in self.EXPORT_STATES:
            for attendee in qs.filter(state=state):
                if attendee.email not in processed:
                    yield [*self.attendee_row(attendee)] + list(self.attendee_summary(attendee.email))
                    processed.append(attendee.email)

    def column_headers(self):
        return [_("Status"), _("Updated"), _("Name"), _("E-mail"),
                *[field.name for field in self.profile_fields]]

    def get_profile_fields(self):
        selected_fields = []

        if self.event.group:
            # get mandatory fields by group
            selected_fields.extend([s.profile_field.id for s in self.event.group.profile_field_settings.all()])
        else:
            # get mandatory fields by site
            selected_fields.extend([f.id for f in ProfileField.objects.filter(is_in_overview=True)])

        # load fields in random order
        fields = {str(f.id): f for f in ProfileField.objects.filter(id__in=selected_fields)}

        # result in same order as in PROFILE_SECTIONS
        result = []
        for section in config.PROFILE_SECTIONS:
            for guid in section['profileFieldGuids']:
                if guid in fields:
                    result.append(fields[guid])
        return result

    def attendee_row(self, attendee):
        return [*self.profile_common_values(attendee),
                *self.profile_field_values(attendee)]

    def profile_common_values(self, attendee):
        return [attendee.format_state(),
                datetime_format(attendee.updated_at, seconds=True),
                attendee.name,
                attendee.email]

    def profile_field_values(self, attendee):
        from user.models import User
        user = attendee.user or User.objects.filter(email=attendee.email).first()
        if not user:
            for _ in self.profile_fields:
                yield ''
        else:
            for field in self.profile_fields:
                user.profile.profile_field_value(field, self.acting_user)
                yield field.value

    def attendee_summary(self, attendee_mail):
        attendee_filters = dict(email=attendee_mail, state='accept')

        main_attendee = EventAttendee.objects.filter(event=self.event, **attendee_filters)
        yield self.event.title if main_attendee.exists() else ""

        attended_sub_events = [*EventAttendee.objects.filter(event__parent=self.event, **attendee_filters).values_list('event_id', flat=True)]
        for guid, title in self.children:
            yield title if guid in attended_sub_events else ''
