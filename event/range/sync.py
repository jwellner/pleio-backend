from core.lib import early_this_morning
from event.models import Event
from event.range.factory import complete_range


class EventRangeSync:

    def __init__(self, event: Event):
        self.event = event
        self.reposition_attendees = RepositionAttendees(event)
        self.last_attendee_date = self.event.start_date

    @property
    def is_update_range(self):
        return self.event.range_settings.get("updateRange")

    @property
    def repeat_until(self):
        return self.event.range_settings.get('repeatUntil')

    @property
    def instance_limit(self):
        return self.event.range_settings.get('instanceLimit')

    def pre_delete(self):
        def _decrement_instance_limit(reference):
            if not self.instance_limit:
                return
            reference.range_settings['instanceLimit'] = self.instance_limit - 1
            reference.save()
            Event.objects.get_range_after(self.event).update_range_limit(reference)
            Event.objects.get_range_before(self.event).update_range_limit(reference)

        previous = Event.objects.get_range_before(self.event).last()
        if previous:
            # Let the previous item cycle one extra time.
            previous.range_cycle += 1
            previous.save()

            _decrement_instance_limit(previous)
        else:
            # Make the next item range master.
            next_master = Event.objects.get_range_after(self.event).first()
            if next_master:
                next_range = Event.objects.get_range_after(next_master)
                next_range.update(range_master=next_master.guid)
                next_master.range_master = None
                next_master.save()

                _decrement_instance_limit(next_master)

    def followup_settings_change(self):
        if self.is_update_range:
            self.apply_changes_to_followups()
            return

        if not self.event.range_ignore:
            self.take_me_out_the_range()

    def apply_changes_to_followups(self):
        self._store_attendees()
        self._update_range()
        self._complete_range()
        self._remove_obsolete_items()
        self._open_range()

    def take_me_out_the_range(self):
        self._ignore_future_range_changes()
        self._open_range()

    def _ignore_future_range_changes(self):
        self.event.range_ignore = True
        self.event.save()

    def _store_attendees(self):
        for event in Event.objects.get_range_after(self.event):
            if event.attendees.all():
                if not self.last_attendee_date or self.last_attendee_date < event.start_date:
                    self.last_attendee_date = event.start_date
                self.reposition_attendees.add(event.start_date, [*event.attendees.all()])

    def _update_range(self):
        Event.objects.get_range_after(self.event).update_range(self.event)
        Event.objects.get_range_before(self.event).update_range_limit(self.event)

    def _complete_range(self):
        complete_range(self.event, self.last_attendee_date)

    def _remove_obsolete_items(self):
        blacklist = Event.objects.none()
        if self.repeat_until is not None:
            blacklist = Event.objects.get_range_after(self.event).filter(start_date__gt=self.repeat_until)
        elif self.instance_limit is not None:
            full_range = Event.objects.get_full_range(self.event)
            if full_range.count() > self.instance_limit:
                blacklist = full_range[:full_range.count() - self.instance_limit]

        self.reposition_attendees.apply(blacklist=[e.guid for e in blacklist])

        for event in blacklist:
            event.delete()

    def _open_range(self):
        Event.objects.get_full_range(self.event).update(range_closed=False)


class RepositionAttendees:

    def __init__(self, starter):
        self.starter = starter
        self.attendee_set = []
        self.blacklist = None

    def _get_queryset(self):
        qs = Event.objects.get_queryset()
        if self.blacklist:
            qs = qs.exclude(id__in=self.blacklist)
        return qs

    def add(self, original_time, attendees):
        self.attendee_set.append((original_time, attendees))

    def apply(self, blacklist):
        self.blacklist = blacklist
        for original_time, attendees in self.attendee_set:
            self._place_attendees(original_time, attendees)

    def _place_attendees(self, original_time, attendees):
        new_event = self._same_day_as(original_time) or self._last_event_in_range()
        # misschien moeten er nieuwe events worden aangemaakt.
        for attendee in attendees:
            if attendee.event == new_event:
                return
            attendee.event = new_event
            attendee.state = 'waitinglist'
            attendee.save()
        new_event.process_waitinglist()

    def _same_day_as(self, original_time):
        return self._get_queryset().get_range_after(self.starter) \
            .filter(start_date__gt=early_this_morning(original_time)).first()

    def _last_event_in_range(self):
        return self._get_queryset().get_range_stopper(self.starter)
