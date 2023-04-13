from django.utils import timezone
from django.utils.timezone import localtime

from core.factories import GroupFactory
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import Event
from user.factories import UserFactory


class AddEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticated_user = UserFactory()
        self.group = GroupFactory(owner=self.authenticated_user, is_membership_on_request=False)
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
        variables = {
            'input': {
                'title': "Simple event",
                'subtype': "event",
                'startDate': str(localtime()),
                'endDate': str(localtime()),
            }
        }

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertTrue(entity['canEdit'])
