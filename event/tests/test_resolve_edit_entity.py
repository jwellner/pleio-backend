from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from event.models import Event, EventSlot
from core.lib import datetime_isoformat
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from django.utils import timezone


class EditEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super(EditEventTestCase, self).setUp()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.group = mixer.blend(Group)

        self.eventPublic = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            start_date=timezone.now(),
            end_date=timezone.now()
        )

        self.data = {
            "input": {
                "guid": self.eventPublic.guid,
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "slotsAvailable": [{'name': 'primary'}],
                "tags": ["tag1", "tag2"],
                "startDate": "2019-10-02T09:00:00+02:00",
                "endDate": "2019-10-02T10:00:00+02:00",
                "maxAttendees": "10",
                "location": "Utrecht",
                "locationLink": "maps.google.nl",
                "locationAddress": "Kerkstraat 10",
                "source": "https://www.pleio.nl",
                "ticketLink": "https://www.pleio-bookings.com/my-first-event",
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
                timeCreated
                timeUpdated
                timePublished
                scheduleArchiveEntity
                scheduleDeleteEntity
                accessId
                writeAccessId
                slotsAvailable {
                    id
                    name
                }
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                owner {
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
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...EventParts
                    }
                }
            }
        """

    def test_edit_event(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["startDate"], "2019-10-02T09:00:00+02:00")
        self.assertEqual(entity["endDate"], "2019-10-02T10:00:00+02:00")
        self.assertEqual(entity["maxAttendees"], variables["input"]["maxAttendees"])
        self.assertEqual(entity["location"], variables["input"]["location"])
        self.assertEqual(entity["locationLink"], variables["input"]["locationLink"])
        self.assertEqual(entity["locationAddress"], variables["input"]["locationAddress"])
        self.assertEqual(entity["source"], variables["input"]["source"])
        self.assertEqual(entity["ticketLink"], variables["input"]["ticketLink"])
        self.assertEqual(entity["attendEventWithoutAccount"], variables["input"]["attendEventWithoutAccount"])
        self.assertEqual(entity["rsvp"], variables["input"]["rsvp"])
        self.assertEqual(entity["qrAccess"], variables["input"]["qrAccess"])
        self.assertDateEqual(entity['timePublished'], variables["input"]["timePublished"])
        self.assertDateEqual(entity['scheduleArchiveEntity'], variables["input"]["scheduleArchiveEntity"])
        self.assertDateEqual(entity['scheduleDeleteEntity'], variables["input"]["scheduleDeleteEntity"])

        self.assertEqual(entity["slotsAvailable"][0]['name'], variables["input"]["slotsAvailable"][0]['name'])
        self.assertIsNotNone(entity["slotsAvailable"][0]['id'])

        self.eventPublic.refresh_from_db()

        self.assertEqual(entity["title"], self.eventPublic.title)
        self.assertEqual(entity['slotsAvailable'][0]['name'], self.eventPublic.slots_available.first().name)
        self.assertEqual(entity['slotsAvailable'][0]['id'], self.eventPublic.slots_available.first().id)
        self.assertEqual(entity["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(entity["startDate"], str(datetime_isoformat(self.eventPublic.start_date)))
        self.assertEqual(entity["endDate"], str(datetime_isoformat(self.eventPublic.end_date)))
        self.assertEqual(entity["maxAttendees"], str(self.eventPublic.max_attendees))
        self.assertEqual(entity["location"], self.eventPublic.location)
        self.assertEqual(entity["locationLink"], self.eventPublic.location_link)
        self.assertEqual(entity["locationAddress"], self.eventPublic.location_address)
        self.assertEqual(entity["ticketLink"], self.eventPublic.ticket_link)

        self.assertEqual(entity["source"], self.eventPublic.external_link)
        self.assertEqual(entity["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)
        self.assertEqual(entity["rsvp"], self.eventPublic.rsvp)
        self.assertEqual(entity["group"], None)
        self.assertEqual(entity["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(entity["timeCreated"], self.eventPublic.created_at.isoformat())
        self.assertEqual(entity["qrAccess"], self.eventPublic.qr_access)

        self.assertDateEqual(entity['timePublished'], str(self.eventPublic.published))
        self.assertDateEqual(entity['scheduleArchiveEntity'], str(self.eventPublic.schedule_archive_after))
        self.assertDateEqual(entity['scheduleDeleteEntity'], str(self.eventPublic.schedule_delete_after))

    def test_edit_event_by_admin(self):
        variables = self.data
        variables["input"]["timeCreated"] = "2018-12-10T23:00:00.000Z"
        variables["input"]["groupGuid"] = self.group.guid
        variables["input"]["ownerGuid"] = self.user2.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["startDate"], "2019-10-02T09:00:00+02:00")
        self.assertEqual(entity["endDate"], "2019-10-02T10:00:00+02:00")
        self.assertEqual(entity["maxAttendees"], variables["input"]["maxAttendees"])
        self.assertEqual(entity["location"], variables["input"]["location"])
        self.assertEqual(entity["source"], variables["input"]["source"])
        self.assertEqual(entity["attendEventWithoutAccount"], variables["input"]["attendEventWithoutAccount"])
        self.assertEqual(entity["rsvp"], variables["input"]["rsvp"])
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

        self.eventPublic.refresh_from_db()

        self.assertEqual(entity["title"], self.eventPublic.title)
        self.assertEqual(entity["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(entity["startDate"], str(datetime_isoformat(self.eventPublic.start_date)))
        self.assertEqual(entity["endDate"], str(datetime_isoformat(self.eventPublic.end_date)))
        self.assertEqual(entity["maxAttendees"], str(self.eventPublic.max_attendees))
        self.assertEqual(entity["location"], self.eventPublic.location)
        self.assertEqual(entity["source"], self.eventPublic.external_link)
        self.assertEqual(entity["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)
        self.assertEqual(entity["rsvp"], self.eventPublic.rsvp)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

    def test_edit_event_group_null_by_admin(self):
        variables = self.data
        variables["input"]["groupGuid"] = None

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["group"], None)

        self.eventPublic.refresh_from_db()
        self.assertEqual(entity["group"], None)

    def test_free_event_from_slots_available(self):
        primary_slot = EventSlot.objects.create(container=self.eventPublic, name="primary")
        secondary_slot = EventSlot.objects.create(container=self.eventPublic, name="secondary")
        mutation = """
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        ... on Event {
                            guid
                            slotsAvailable {
                                id
                                name
                            }
                        }
                    }
                }
            }
        """
        self.graphql_client.force_login(self.admin)
        response = self.graphql_client.post(mutation, {
            'input': {
                'guid': self.eventPublic.guid,
                'slotsAvailable': [{'id': primary_slot.id,
                                    'delete': True}],
            }
        })
        self.assertEqual(response['data']['editEntity']['entity']['guid'], self.eventPublic.guid)
        self.assertEqual(response['data']['editEntity']['entity']['slotsAvailable'][0]['id'], secondary_slot.id)
        self.assertEqual(response['data']['editEntity']['entity']['slotsAvailable'][0]['name'], secondary_slot.name)
        self.assertEqual(len(response['data']['editEntity']['entity']['slotsAvailable']), 1)

    def test_assign_main_event_to_slot(self):
        mutation = """
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        ... on Event {
                            guid
                            slot {
                                id
                                name
                            }
                        }
                    }
                }
            }
        """

        with self.assertGraphQlError('subevent_only_operation'):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(mutation, {
                'input': {
                    'guid': self.eventPublic.guid,
                    'slot': {'id': 1}
                }
            })

    def test_assign_subevent_to_slot(self):
        primary_slot = EventSlot.objects.create(container=self.eventPublic, name="primary")
        event = mixer.blend(Event,
                            parent=self.eventPublic,
                            start_date=self.eventPublic.start_date,
                            end_date=self.eventPublic.end_date)

        mutation = """
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        ... on Event {
                            guid
                            slot {
                                id
                                name
                            }
                        }
                    }
                }
            }
        """
        self.graphql_client.force_login(self.admin)
        response = self.graphql_client.post(mutation, {
            'input': {
                'guid': event.guid,
                'slot': {'id': primary_slot.id}
            }
        })

        self.assertEqual(response['data']['editEntity']['entity']['slot']['id'], primary_slot.id)
        self.assertEqual(response['data']['editEntity']['entity']['slot']['name'], primary_slot.name)

    def test_free_subevent_from_slot(self):
        primary_slot = EventSlot.objects.create(container=self.eventPublic, name="primary")
        subevent = mixer.blend(Event,
                               parent=self.eventPublic,
                               slot=primary_slot,
                               start_date=self.eventPublic.start_date,
                               end_date=self.eventPublic.end_date)

        mutation = """
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        ... on Event {
                            guid
                            slot {
                                id
                                name
                            }
                        }
                    }
                }
            }
        """
        self.graphql_client.force_login(self.admin)
        response = self.graphql_client.post(mutation, {
            'input': {
                'guid': subevent.guid,
                'slot': {'id': None}
            }
        })

        self.assertEqual(response['data']['editEntity']['entity']['guid'], subevent.guid)
        self.assertEqual(response['data']['editEntity']['entity']['slot'], None)
