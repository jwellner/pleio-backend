from unittest import mock

from django.utils import timezone
from django.utils.timezone import timedelta

from core.lib import early_this_morning
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import Event, EventAttendee
from event.range.factory import EventRangeFactory, complete_range
from event.range.sync import EventRangeSync
from user.factories import UserFactory
from user.models import User


class TestRangeFollowupTestCase(PleioTenantTestCase):
    DEFAULT_TITLE = "Range event"
    DEFAULT_CONTENT = "Range event content"

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.range_master = EventFactory(owner=self.owner,
                                         title=self.DEFAULT_TITLE,
                                         rich_description=self.DEFAULT_CONTENT,
                                         start_date=timezone.now(),
                                         range_starttime=timezone.now(),
                                         range_settings={
                                             "type": "dayOfTheWeek",
                                             "interval": 1
                                         })
        self.range_follower = EventRangeFactory(self.range_master).create_next_event()
        self.range_follower2 = EventRangeFactory(self.range_master).create_next_event()
        self.range_follower3 = EventRangeFactory(self.range_master).create_next_event()
        self.range_follower4 = EventRangeFactory(self.range_master).create_next_event()
        self.range_follower5 = EventRangeFactory(self.range_master).create_next_event()
        self.range_follower6 = EventRangeFactory(self.range_master).create_next_event()
        Event.objects.get_full_range(self.range_master).update(range_closed=True)

    def reload_events(self):
        self.range_master.refresh_from_db()
        self.range_follower.refresh_from_db()
        self.range_follower2.refresh_from_db()
        self.range_follower3.refresh_from_db()
        self.range_follower4.refresh_from_db()
        self.range_follower5.refresh_from_db()
        self.range_follower6.refresh_from_db()

    def test_create_new_starter(self):
        # Given.
        self.range_follower5.range_ignore = True
        self.range_follower5.save()
        self.range_follower3.title = "new title"
        self.range_follower3.save()

        # Event is closed for event processing
        self.assertFalse(Event.objects.filter_range_events().filter(id=self.range_master.id).exists())

        # When.
        sync = EventRangeSync(self.range_follower3)
        sync.apply_changes_to_followups()
        self.reload_events()

        # Then earlier events are unchanged
        self.assertNotEqual(self.range_master.title, self.range_follower3.title)
        self.assertNotEqual(self.range_follower.title, self.range_follower3.title)
        self.assertNotEqual(self.range_follower2.title, self.range_follower3.title)

        # Events that are no longer in the range are unchanged
        self.assertNotEqual(self.range_follower5.title, self.range_follower3.title)

        # Future events in the range are updated.
        self.assertEqual(self.range_follower4.title, self.range_follower3.title)
        self.assertEqual(self.range_follower6.title, self.range_follower3.title)

        # Event is opened for event processing again
        self.assertTrue(Event.objects.filter_range_events().filter(id=self.range_master.id).exists())

    def test_take_the_range_master_out_of_the_range(self):
        # Given.
        sync = EventRangeSync(self.range_master)

        # Event is closed for event processing
        self.assertFalse(Event.objects.filter_range_events().filter(id=self.range_master.id).exists())

        # When.
        sync.take_me_out_the_range()
        self.reload_events()

        # Then...
        self.assertEqual(self.range_master.range_ignore, True)

        # Event is opened for event processing again
        self.assertTrue(Event.objects.filter_range_events().filter(id=self.range_master.id).exists())


class TestRangeFollowupUpdateInstanceLimitTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory(email="event.owner@example.com")
        self.range_master = EventFactory(owner=self.owner,
                                         title="Foo",
                                         start_date=timezone.now(),
                                         range_starttime=timezone.now(),
                                         range_settings={
                                             "type": "daily",
                                             "interval": 1,
                                             "instanceLimit": 10,
                                             "updateRange": True,
                                         })
        # Create 10 items (full range)
        complete_range(self.range_master, timezone.now(), 10)

    def test_reduce_number_of_repetitions_to_9(self):
        self.range_master.range_settings['instanceLimit'] = 9
        self.range_master.save()

        self.assertEqual(Event.objects.count(), 10)
        sync = EventRangeSync(self.range_master)
        sync.followup_settings_change()

        self.assertEqual(Event.objects.count(), 9)
        self.assertTrue(Event.objects.filter(pk=self.range_master.guid).exists())

    def test_reduce_number_of_repetitions_to_1(self):
        self.range_master.range_settings['instanceLimit'] = 1
        self.range_master.save()

        self.assertEqual(Event.objects.count(), 10)
        sync = EventRangeSync(self.range_master)
        sync.followup_settings_change()

        self.assertEqual(Event.objects.count(), 1)
        self.assertTrue(Event.objects.filter(pk=self.range_master.guid).exists())

    def test_increase_number_of_repetitions_to_15(self):
        changing_event = Event.objects.get_full_range(self.range_master).first()
        changing_event.range_settings['instanceLimit'] = 15
        changing_event.save()

        self.assertEqual(Event.objects.count(), 10)
        sync = EventRangeSync(changing_event)
        sync.followup_settings_change()

        self.assertEqual(Event.objects.count(), 10)
        self.assertTrue(Event.objects.filter(pk=self.range_master.guid).exists())
        self.range_master.refresh_from_db()
        self.assertEqual(self.range_master.range_settings['instanceLimit'], 15)

    def test_increase_number_of_repetitions_to_unlimited(self):
        changing_event = Event.objects.get_full_range(self.range_master).first()
        changing_event.range_settings['instanceLimit'] = None
        changing_event.save()

        self.assertEqual(Event.objects.count(), 10)
        sync = EventRangeSync(changing_event)
        sync.followup_settings_change()

        self.assertEqual(Event.objects.count(), 10)
        self.assertTrue(Event.objects.filter(pk=self.range_master.guid).exists())
        self.range_master.refresh_from_db()
        self.assertEqual(self.range_master.range_settings['instanceLimit'], None)


class TestRangeFollowupUpdateRepeatUntilTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory(email="event.owner@example.com")
        self.master_date = timezone.now() - timedelta(days=(10 - 1))
        self.range_master = EventFactory(owner=self.owner,
                                         title="Foo",
                                         start_date=self.master_date,
                                         range_starttime=self.master_date,
                                         range_settings={
                                             "type": "daily",
                                             "interval": 1,
                                             "repeatUntil": timezone.now().isoformat(),
                                             "updateRange": True,
                                         })
        complete_range(self.range_master, timezone.now())

    def test_move_repeat_until_earlier(self):
        self.range_master.range_settings['repeatUntil'] = (timezone.now() - timedelta(days=5)).isoformat()
        self.range_master.save()

        self.assertEqual(Event.objects.count(), 10)
        sync = EventRangeSync(self.range_master)
        sync.followup_settings_change()

        self.assertEqual(Event.objects.count(), 5)
        self.assertTrue(Event.objects.filter(pk=self.range_master.guid).exists())

    def test_move_repeat_until_later(self):
        changing_event = Event.objects.get_full_range(self.range_master).first()
        changing_event.range_settings['repeatUntil'] = (timezone.now() + timedelta(days=5)).isoformat()
        changing_event.save()

        self.assertEqual(Event.objects.count(), 10)
        sync = EventRangeSync(changing_event)
        sync.followup_settings_change()

        self.assertEqual(Event.objects.count(), 10)
        self.assertTrue(Event.objects.filter(pk=self.range_master.guid).exists())
        self.range_master.refresh_from_db()
        self.assertEqual(self.range_master.range_settings['repeatUntil'], changing_event.range_settings['repeatUntil'])

    def test_drop_repeat_until_setting(self):
        changing_event = Event.objects.get_full_range(self.range_master).first()
        changing_event.range_settings['repeatUntil'] = None
        changing_event.save()

        self.assertEqual(Event.objects.count(), 10)
        sync = EventRangeSync(changing_event)
        sync.followup_settings_change()

        self.assertEqual(Event.objects.count(), 10)
        self.assertTrue(Event.objects.filter(pk=self.range_master.guid).exists())
        self.range_master.refresh_from_db()
        self.assertEqual(self.range_master.range_settings['repeatUntil'], None)


class TestRangeFollowupSettingsChangeTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.event = EventFactory(owner=self.owner,
                                  range_settings={})

    def tearDown(self):
        self.event.delete()
        self.owner.delete()
        super().tearDown()

    @mock.patch("event.range.sync.EventRangeSync.apply_changes_to_followups")
    @mock.patch("event.range.sync.EventRangeSync.take_me_out_the_range")
    def test_clean_call(self, take_me_out_the_range, apply_changes_to_followups):
        sync = EventRangeSync(self.event)
        sync.followup_settings_change()

        self.assertTrue(take_me_out_the_range.called)
        self.assertFalse(apply_changes_to_followups.called)

    @mock.patch("event.range.sync.EventRangeSync.apply_changes_to_followups")
    @mock.patch("event.range.sync.EventRangeSync.take_me_out_the_range")
    def test_apply_changes_to_followups(self, take_me_out_the_range, apply_changes_to_followups):
        self.event.range_settings['updateRange'] = True

        sync = EventRangeSync(self.event)
        sync.followup_settings_change()

        self.assertFalse(take_me_out_the_range.called)
        self.assertTrue(apply_changes_to_followups.called)

    @mock.patch("event.range.sync.EventRangeSync.apply_changes_to_followups")
    @mock.patch("event.range.sync.EventRangeSync.take_me_out_the_range")
    def test_take_me_out_the_range(self, take_me_out_the_range, apply_changes_to_followups):
        self.event.range_ignore = True

        sync = EventRangeSync(self.event)
        sync.followup_settings_change()

        self.assertFalse(take_me_out_the_range.called)
        self.assertFalse(apply_changes_to_followups.called)


class TestUpdateRangeIntervalTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.START_DATE = timezone.now()
        self.HALFWAY_DATE = early_this_morning(self.START_DATE + timedelta(weeks=8, days=1))
        self.END_DATE = early_this_morning(self.START_DATE + timedelta(weeks=10, days=1))
        self.range_master = EventFactory(owner=self.owner,
                                         start_date=self.START_DATE,
                                         range_starttime=self.START_DATE,
                                         range_settings={
                                             "type": "dayOfTheWeek",
                                             "interval": 1,
                                             "repeatUntil": self.END_DATE.isoformat(),
                                         })
        complete_range(self.range_master, self.END_DATE)

        self.all_events = Event.objects.get_full_range(self.range_master).order_by('range_starttime')

        self.last_event = self.all_events[10]
        self.last_time = self.last_event.range_starttime
        self.last_guid = self.last_event.guid
        self.last_attendees = [
            EventAttendee.objects.create(user=UserFactory(email="no1@last.com"),
                                         event=self.all_events[10],
                                         state="accept"),
        ]
        self.forlast_event = self.all_events[6]
        self.forlast_time = self.forlast_event.range_starttime
        self.forlast_guid = self.forlast_event.guid
        self.forlast_attendees = [
            EventAttendee.objects.create(user=UserFactory(email="no1@forlast.com"),
                                         event=self.forlast_event,
                                         state="accept"),
            EventAttendee.objects.create(user=UserFactory(email="no2@forlast.com"),
                                         event=self.forlast_event,
                                         state="accept"),
        ]

        self.changing_event = self.all_events[4]
        self.changing_time = self.changing_event.range_starttime
        self.changing_guid = self.changing_event.guid
        self.changing_attendees = [
            EventAttendee.objects.create(user=UserFactory(email="no1@changing.com"),
                                         event=self.changing_event,
                                         state="accept"),
            EventAttendee.objects.create(user=UserFactory(email="no2@changing.com"),
                                         event=self.changing_event,
                                         state="accept"),
            EventAttendee.objects.create(user=UserFactory(email="no3@changing.com"),
                                         event=self.changing_event,
                                         state="accept"),
        ]

        self.per_time_events = {e.range_starttime: e for e in Event.objects.get_full_range(self.range_master)}

    def tearDown(self):
        for attendee in EventAttendee.objects.all():
            attendee.delete()
        for event in Event.objects.all():
            event.delete()
        for user in User.objects.all():
            user.delete()

        super().tearDown()

    def test_move_attendees(self):
        # given
        self.changing_event.range_settings['interval'] = 2
        self.changing_event.range_settings['updateRange'] = True
        self.changing_event.save()
        initial_event_guids = {str(guid) for guid in Event.objects.get_full_range(self.range_master).ids()}

        # when
        sync = EventRangeSync(self.changing_event)
        sync.followup_settings_change()

        # Then, less items should be in the range in total.
        event_guids = {str(guid) for guid in Event.objects.get_full_range(self.range_master).ids()}
        self.assertNotEqual(initial_event_guids, event_guids)
        self.assertEqual(initial_event_guids & event_guids, event_guids)

        # Then, should have removed the last items in the range
        try:
            self.last_event.refresh_from_db()
            self.fail("Last event in the row unexpectedly still exists")
        except Event.DoesNotExist:
            pass

        # Then, based on the time, the attendees are moved to another event
        per_time_events = {e.range_starttime: e for e in Event.objects.get_full_range(self.range_master)}
        assert self.last_time in per_time_events
        last_mails = {a.user.email for a in per_time_events[self.last_time].attendees.all()}
        self.assertEqual(last_mails, {'no1@last.com'})

        assert self.forlast_time in per_time_events
        forlast_mails = {a.user.email for a in per_time_events[self.forlast_time].attendees.all()}
        self.assertEqual(forlast_mails, {'no1@forlast.com', 'no2@forlast.com'})

        # Then the changing event has the same attendees.
        assert self.changing_time in per_time_events
        changing_mails = {a.user.email for a in per_time_events[self.changing_time].attendees.all()}
        self.assertEqual(changing_mails, {'no1@changing.com', 'no2@changing.com', 'no3@changing.com'})

    def test_move_attendees_to_last(self):
        # Given
        self.changing_event.range_settings['repeatUntil'] = self.changing_event.range_starttime.isoformat()
        self.changing_event.range_settings['updateRange'] = True
        self.changing_event.save()

        # When.
        sync = EventRangeSync(self.changing_event)
        sync.followup_settings_change()

        # Then.
        self.assertEqual({a.user.email for a in self.changing_event.attendees.all()},
                         {'no1@last.com',
                          'no1@forlast.com', 'no2@forlast.com',
                          'no1@changing.com', 'no2@changing.com', 'no3@changing.com'})


class TestPreDeleteSyncBehaviourTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.range_master = EventFactory(owner=self.owner,
                                         title="Repeating event",
                                         rich_description=self.tiptap_paragraph("This event will repeat until 3 instances"),
                                         start_date=timezone.now(),
                                         range_starttime=timezone.now(),
                                         range_settings={
                                             "type": "dayOfTheWeek",
                                             "interval": 1,
                                             "instanceLimit": 3,
                                         })
        complete_range(self.range_master, timezone.now(), 3)

    def tearDown(self):
        for event in Event.objects.all():
            event.delete()
        self.owner.delete()
        super().tearDown()

    def test_delete_third_item(self):
        # Given.
        second = Event.objects.get_range_after(self.range_master)[0]
        third = Event.objects.get_range_after(self.range_master)[1]
        sync = EventRangeSync(third)

        # When.
        sync.pre_delete()
        self.range_master.refresh_from_db()
        second.refresh_from_db()

        # Then
        self.assertEqual(self.range_master.range_cycle, 1)
        self.assertEqual(second.range_cycle, 2)
        self.assertEqual(self.range_master.range_settings['instanceLimit'], 2)

    def test_delete_first_item(self):
        # Given.
        next_master = Event.objects.get_range_after(self.range_master).first()
        sync = EventRangeSync(self.range_master)

        # When.
        sync.pre_delete()
        self.range_master.refresh_from_db()
        next_master.refresh_from_db()

        # Then
        self.assertEqual(next_master.range_cycle, 1)
        self.assertEqual(next_master.range_settings['instanceLimit'], 2)
        self.assertEqual(Event.objects.get_range_before(next_master).count(), 0)
        self.assertEqual(Event.objects.get_range_after(next_master).count(), 1)
