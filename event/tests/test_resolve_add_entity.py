from unittest import mock

from django.utils.timezone import localtime, timedelta

from blog.factories import BlogFactory
from core.factories import GroupFactory
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import Event
from core.constances import ACCESS_TYPE
from django.utils import timezone

from user.factories import UserFactory
from user.models import User


class AddEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticated_user = UserFactory()
        self.group = GroupFactory(owner=self.authenticated_user, is_membership_on_request=False)
        self.suggested_item = BlogFactory(owner=self.authenticated_user)
        self.eventPublic = EventFactory(owner=self.authenticated_user)
        self.eventGroupPublic = EventFactory(owner=self.authenticated_user, group=self.group)

        self.data = {
            "input": {
                "subtype": "event",
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "startDate": "2019-10-02T09:00:00+02:00",
                "endDate": "2019-10-02T10:00:00+02:00",
                "ticketLink": "https://www.pleio.nl",
                "maxAttendees": "10",
                "location": "Utrecht",
                "locationLink": "maps.google.nl",
                "locationAddress": "Kerkstraat 10",
                "source": "https://www.pleio.nl",
                "attendEventWithoutAccount": True,
                "rsvp": True,
                "qrAccess": True,
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
                "attendeeWelcomeMailSubject": "Welcome subject",
                "attendeeWelcomeMailContent": "Welcome content",
                "suggestedItems": [self.suggested_item.guid]
            }
        }
        self.mutation = """
            fragment EventParts on Event {
                title
                richDescription
                parent {
                    guid
                }
                hasChildren
                timeCreated
                timeUpdated
                timePublished
                scheduleArchiveEntity
                scheduleDeleteEntity
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                rsvp
                source
                ticketLink
                attendEventWithoutAccount
                startDate
                endDate
                location
                locationLink
                locationAddress
                maxAttendees
                qrAccess
                attendeeWelcomeMailSubject
                attendeeWelcomeMailContent
                suggestedItems {
                    guid
                }
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                        guid
                        status
                        ...EventParts
                    }
                }
            }
        """
        self.least_variables = {
            'input': {
                'title': "Simple event",
                'subtype': "event",
                'startDate': str(localtime()),
                'endDate': str(localtime()),
            }
        }

    def tearDown(self):
        self.suggested_item.delete()
        self.eventPublic.delete()
        self.eventGroupPublic.delete()
        self.group.delete()
        self.authenticated_user.delete()
        super().tearDown()

    def test_add_event(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["location"], variables["input"]["location"])
        self.assertEqual(entity["locationLink"], variables["input"]["locationLink"])
        self.assertEqual(entity["locationAddress"], variables["input"]["locationAddress"])
        self.assertEqual(entity["rsvp"], variables["input"]["rsvp"])
        self.assertEqual(entity["source"], variables["input"]["source"])
        self.assertEqual(entity["ticketLink"], variables["input"]["ticketLink"])
        self.assertEqual(entity["startDate"], "2019-10-02T09:00:00+02:00")
        self.assertEqual(entity["endDate"], "2019-10-02T10:00:00+02:00")
        self.assertEqual(entity["attendEventWithoutAccount"], variables["input"]["attendEventWithoutAccount"])
        self.assertEqual(entity["maxAttendees"], variables["input"]["maxAttendees"])
        self.assertEqual(entity["qrAccess"], variables["input"]["qrAccess"])
        self.assertDateEqual(entity['timePublished'], variables["input"]["timePublished"])
        self.assertDateEqual(entity['scheduleArchiveEntity'], variables["input"]["scheduleArchiveEntity"])
        self.assertDateEqual(entity['scheduleDeleteEntity'], variables["input"]["scheduleDeleteEntity"])
        self.assertEqual(entity['attendeeWelcomeMailSubject'], variables['input']['attendeeWelcomeMailSubject'])
        self.assertEqual(entity['attendeeWelcomeMailContent'], variables['input']['attendeeWelcomeMailContent'])
        self.assertEqual(entity['suggestedItems'], [{"guid": self.suggested_item.guid}])

    def test_add_event_to_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)

    def test_add_event_to_parent(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.eventPublic.guid

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["hasChildren"], False)
        self.assertEqual(entity["parent"]["guid"], self.eventPublic.guid)

        self.eventPublic.refresh_from_db()

        self.assertTrue(self.eventPublic.has_children())
        self.assertEqual(self.eventPublic.children.first().guid, entity["guid"])

    def test_add_event_to_parent_with_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.eventGroupPublic.guid

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["hasChildren"], False)
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["parent"]["guid"], self.eventGroupPublic.guid)

        self.eventGroupPublic.refresh_from_db()

        self.assertTrue(self.eventGroupPublic.has_children())
        self.assertEqual(self.eventGroupPublic.children.first().guid, entity["guid"])

    def test_add_event_with_attachment(self):
        attachment = self.file_factory(self.relative_path(__file__, ['assets', 'landscape.jpeg']))

        variables = self.data
        variables["input"]["richDescription"] = self.tiptap_attachment(attachment)

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        event = Event.objects.get(id=entity["guid"])
        self.assertTrue(event.attachments.filter(file_id=attachment.id).exists())

    def test_add_minimal_entity(self):
        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, self.least_variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertTrue(entity['canEdit'])


class TestAddRangeEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.now = timezone.datetime.fromisoformat("2019-01-01T09:00:00+01:00")
        self.timezone_now = mock.patch("django.utils.timezone.now").start()
        self.timezone_now.return_value = self.now

        self.authenticated_user = UserFactory()
        self.variables = {
            "input": {
                "subtype": "event",
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "startDate": (self.now + timedelta(days=1)).isoformat(),
                "endDate": (self.now + timedelta(days=1, hours=1)).isoformat(),
                "rangeSettings": {
                    "type": "daily",
                    "interval": 3,
                    "updateRange": True,
                }
            },
        }
        self.mutation = """
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                        guid
                        ... on Event {
                            title
                            startDate
                            endDate
                            rangeSettings {
                                repeatUntil
                                instanceLimit
                                type
                                interval
                                isIgnored
                            }
                        }
                    }
                }
            }
        """

    def tearDown(self):
        for event in Event.objects.all():
            event.delete()
        self.authenticated_user.delete()
        super().tearDown()

    def test_add_range_event(self):
        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result['data']['addEntity']['entity']
        self.assertEqual(entity['title'], self.variables['input']['title'])

        range_settings = entity['rangeSettings']
        self.assertEqual({*range_settings.keys()}, {'repeatUntil',
                                                    'instanceLimit',
                                                    'type',
                                                    'interval',
                                                    'isIgnored'})
        self.assertEqual(range_settings['repeatUntil'], None)

        self.assertEqual(range_settings['repeatUntil'], None)
        self.assertEqual(range_settings['instanceLimit'], None)
        self.assertEqual(range_settings['type'], self.variables['input']['rangeSettings']['type'])
        self.assertEqual(range_settings['interval'], self.variables['input']['rangeSettings']['interval'])
        self.assertEqual(range_settings['isIgnored'], False)

        db_entity = Event.objects.get(pk=entity['guid'])
        self.assertIsNotNone(db_entity.range_starttime)
        self.assertEqual(db_entity.range_starttime, db_entity.start_date)

    def test_add_range_with_invalid_repeat_until_date(self):
        self.variables['input']['rangeSettings']['repeatUntil'] = self.now.isoformat()

        with self.assertGraphQlError('event_invalid_repeat_until_date'):
            self.graphql_client.force_login(self.authenticated_user)
            self.graphql_client.post(self.mutation, self.variables)

    def test_add_range_with_valid_repeat_until_date(self):
        self.variables['input']['rangeSettings']['repeatUntil'] = (self.now + timedelta(days=5)).isoformat()

        self.graphql_client.force_login(self.authenticated_user)
        self.graphql_client.post(self.mutation, self.variables)
