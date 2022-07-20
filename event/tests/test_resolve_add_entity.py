from django.utils.timezone import localtime

from core.models.attachment import Attachment
import json
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from event.models import Event
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from django.utils import timezone


class AddEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddEventTestCase, self).setUp()
        self.authenticated_user = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticated_user, is_membership_on_request=False)
        self.group.join(self.authenticated_user, 'owner')

        self.eventPublic = mixer.blend(Event,
                                       owner=self.authenticated_user,
                                       read_access=[ACCESS_TYPE.public],
                                       write_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)])

        self.eventGroupPublic = mixer.blend(Event,
                                            owner=self.authenticated_user,
                                            read_access=[ACCESS_TYPE.public],
                                            write_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
                                            group=self.group)

        self.data = {
            "input": {
                "type": "object",
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
            }
        }
        self.mutation = """
            fragment EventParts on Event {
                title
                richDescription
                parent {
                    guid
                }
                slot {
                    name,
                }
                slotsAvailable {
                    id
                    name
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
        attachment = mixer.blend(Attachment)

        variables = self.data
        variables["input"]["richDescription"] = json.dumps(
            {'type': 'file', 'attrs': {'url': f"/attachment/entity/{attachment.id}"}})

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        event = Event.objects.get(id=entity["guid"])
        self.assertTrue(event.attachments.filter(id=attachment.id).exists())

    def test_add_main_event_with_slot_should_fail(self):
        variables = self.data
        variables['input']['slot'] = {'id': 1}

        with self.assertGraphQlError('subevent_only_operation'):
            self.graphql_client.force_login(self.authenticated_user)
            self.graphql_client.post(self.mutation, variables)

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
