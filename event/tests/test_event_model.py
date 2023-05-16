from unittest import mock

from django.utils import timezone

from blog.factories import BlogFactory
from core.lib import datetime_utciso
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import Event
from event.range.factory import EventRangeFactory
from user.factories import UserFactory


class TestEventModelTestCase(PleioTenantTestCase):
    maxDiff = None

    TITLE = 'Some event'
    CONTENT = 'Event content'
    ABSTRACT = 'Abstract summary'
    SUBJECT = 'Welcome you!'
    WELCOME = 'Welcome! Hope you enjoy.'
    EXTERNAL_LINK = "https://some/where"
    LOCATION = "Some Inn"
    LOCATION_ADDRESS = "5th av. 22nd st."
    LOCATION_LINK = "https://maps.google.com/some-where"
    TICKET_LINK = "https://tickets/dot/com"

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.parent = EventFactory(owner=self.owner)
        self.suggested_item = BlogFactory(owner=self.owner)
        self.entity = EventFactory(owner=self.owner,
                                   parent=self.parent,
                                   title=self.TITLE,
                                   rich_description=self.CONTENT,
                                   abstract=self.ABSTRACT,
                                   attendee_welcome_mail_subject=self.SUBJECT,
                                   attendee_welcome_mail_content=self.WELCOME,
                                   external_link=self.EXTERNAL_LINK,
                                   location=self.LOCATION,
                                   location_address=self.LOCATION_ADDRESS,
                                   location_link=self.LOCATION_LINK,
                                   ticket_link=self.TICKET_LINK,
                                   suggested_items=[self.suggested_item.guid])

    def tearDown(self):
        super().tearDown()

    @mock.patch("core.models.Entity.serialize")
    def test_serialize(self, serialize):
        serialize.return_value = {}
        serialized = self.entity.serialize()

        self.assertEqual(serialized, {
            'title': self.TITLE,
            'richDescription': self.CONTENT,
            'abstract': self.ABSTRACT,
            'attendeeWelcomeMailSubject': self.SUBJECT,
            'attendeeWelcomeMailContent': self.WELCOME,
            'attendEventWithoutAccount': False,
            'enableMaybeAttendEvent': True,
            'externalLink': self.EXTERNAL_LINK,
            'location': self.LOCATION,
            'locationAddress': self.LOCATION_ADDRESS,
            'locationLink': self.LOCATION_LINK,
            'maxAttendees': None,
            'parentGuid': self.entity.parent.guid,
            'qrAccess': False,
            'rsvp': False,
            'sharedViaSlot': [],
            'slotsAvailable': [],
            'suggestedItems': [self.suggested_item.guid],
            'ticketLink': self.TICKET_LINK,
            'startDate': datetime_utciso(self.entity.start_date),
            'endDate': datetime_utciso(self.entity.end_date),
        })

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['richDescription'] = "new %s" % self.CONTENT
        expected['abstract'] = "new %s" % self.ABSTRACT

        self.entity.map_rich_text_fields(lambda v: "new %s" % v)
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)

    @mock.patch("event.range.sync.EventRangeSync.pre_delete")
    def test_non_recurring_event_delete(self, pre_delete):
        self.entity.delete()

        self.assertFalse(pre_delete.called)


class TestEventQueryset(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.range_master = EventFactory(owner=self.owner,
                                         title="Recurring event",
                                         start_date=timezone.now(),
                                         range_starttime=timezone.now(),
                                         range_settings={
                                             "type": "dayOfTheWeek",
                                             "interval": 1
                                         })
        self.range_follower1 = EventRangeFactory(self.range_master).create_next_event()
        self.range_follower2 = EventRangeFactory(self.range_master).create_next_event()
        self.range_follower3 = EventRangeFactory(self.range_master).create_next_event()
        self.not_a_range = EventFactory(owner=self.owner,
                                        title="Not a recurring event")

    def test_ids(self):
        self.assertEqual({e for e in Event.objects.ids()}, {
            self.not_a_range.id,
            self.range_master.id,
            self.range_follower1.id,
            self.range_follower2.id,
            self.range_follower3.id
        })

    def test_get_full_range(self):
        from_master = Event.objects.get_full_range(self.range_master)
        from_follower = Event.objects.get_full_range(self.range_follower2)
        self.assertEqual({*from_follower.ids()}, {*from_master.ids()})
        self.assertEqual(from_follower.count(), 4)

    def test_get_full_range_not_a_range(self):
        self.assertEqual(Event.objects.get_full_range(self.not_a_range).count(), 0)

    def test_get_range_after(self):
        self.assertEqual([*Event.objects.get_range_after(self.range_master)], [
            self.range_follower1,
            self.range_follower2,
            self.range_follower3,
        ])
        self.assertEqual([*Event.objects.get_range_after(self.range_follower1)], [
            self.range_follower2,
            self.range_follower3,
        ])
        self.assertEqual([*Event.objects.get_range_after(self.range_follower2)], [
            self.range_follower3,
        ])
        self.assertEqual([*Event.objects.get_range_after(self.range_follower3)], [])
        self.assertEqual([*Event.objects.get_range_after(self.not_a_range)], [])

    def test_get_range_before(self):
        self.assertEqual([*Event.objects.get_range_before(self.range_master)], [])
        self.assertEqual([*Event.objects.get_range_before(self.range_follower1)], [
            self.range_master,
        ])
        self.assertEqual([*Event.objects.get_range_before(self.range_follower2)], [
            self.range_master,
            self.range_follower1,
        ])
        self.assertEqual([*Event.objects.get_range_before(self.range_follower3)], [
            self.range_master,
            self.range_follower1,
            self.range_follower2,
        ])
        self.assertEqual([*Event.objects.get_range_before(self.not_a_range)], [])

    def test_get_range_stopper(self):
        self.assertEqual(Event.objects.get_range_stopper(self.range_master), self.range_follower3)
        self.assertEqual(Event.objects.get_range_stopper(self.range_follower1), self.range_follower3)
        self.assertEqual(Event.objects.get_range_stopper(self.range_follower2), self.range_follower3)
        self.assertEqual(Event.objects.get_range_stopper(self.range_follower3), self.range_follower3)

        self.assertEqual(Event.objects.get_range_stopper(self.not_a_range), None)

    def test_filter_range_events(self):
        self.assertEqual([*Event.objects.filter_range_events().ids()], [self.range_master.id])

    def test_filter_closed_range_events(self):
        self.range_master.range_closed = True
        self.range_master.save()

        self.assertEqual([*Event.objects.filter_range_events().ids()], [])

    def test_get_last_referable(self):
        self.assertEqual(Event.objects.get_range_last_referable(self.range_master), self.range_follower3)
        self.assertEqual(Event.objects.get_range_last_referable(self.range_follower1), self.range_follower3)
        self.assertEqual(Event.objects.get_range_last_referable(self.range_follower2), self.range_follower3)
        self.assertEqual(Event.objects.get_range_last_referable(self.range_follower3), self.range_follower3)

        self.assertEqual(Event.objects.get_range_last_referable(self.not_a_range), None)

    def test_get_last_referable_is_ignored(self):
        self.range_follower3.range_ignore = True
        self.range_follower3.save()

        self.assertEqual(Event.objects.get_range_last_referable(self.range_master), self.range_follower2)
        self.assertEqual(Event.objects.get_range_last_referable(self.range_follower1), self.range_follower2)
        self.assertEqual(Event.objects.get_range_last_referable(self.range_follower2), self.range_follower2)
        self.assertEqual(Event.objects.get_range_last_referable(self.range_follower3), self.range_follower2)

    def test_extra_cycle_update_range(self):
        # Given.
        self.range_master.range_cycle = 3
        self.range_master.save()
        original_dates = [e.range_starttime for e in Event.objects.get_full_range(self.range_master).order_by('range_starttime')]

        # When.
        Event.objects.get_range_after(self.range_master).update_range(self.range_master)
        new_dates = [e.range_starttime for e in Event.objects.get_full_range(self.range_master).order_by('range_starttime')]

        # Then.
        self.assertNotEqual(new_dates, original_dates)
        self.assertEqual(new_dates[0], original_dates[0])
        self.assertEqual(new_dates[1], original_dates[3])
