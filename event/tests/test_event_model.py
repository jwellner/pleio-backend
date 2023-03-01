from unittest import mock

from core.lib import datetime_utciso
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
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
                                   ticket_link=self.TICKET_LINK)

    def tearDown(self):
        self.entity.delete()
        self.parent.delete()
        self.owner.delete()
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
