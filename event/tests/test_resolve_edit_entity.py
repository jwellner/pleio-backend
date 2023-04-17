from unittest import mock

from django.utils import timezone

from blog.factories import BlogFactory
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.range.factory import EventRangeFactory, complete_range
from user.models import User
from event.models import Event
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer


class EditEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.group = mixer.blend(Group)
        self.suggested_item = BlogFactory(owner=self.authenticatedUser)

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
                "attendeeWelcomeMailSubject": "Mail Subject",
                "attendeeWelcomeMailContent": "Welcome Content",
                "suggestedItems": [self.suggested_item.guid]
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
                    name
                    subEventGuids
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
                attendeeWelcomeMailSubject
                attendeeWelcomeMailContent
                suggestedItems {
                    guid
                }
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

    def tearDown(self):
        self.eventPublic.delete()
        self.suggested_item.delete()
        self.group.delete()

        self.authenticatedUser.delete()
        self.user2.delete()
        self.admin.delete()

        super().tearDown()

    def test_edit_event(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)
        self.assertMutationProcessedCorrectly(result)

    def test_edit_event_by_admin(self):
        self.data["input"]["timeCreated"] = "2018-12-10T23:00:00.000Z"
        self.data["input"]["groupGuid"] = self.group.guid
        self.data["input"]["ownerGuid"] = self.user2.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.data)

        self.assertMutationProcessedCorrectly(result)

        # And...
        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

    def assertMutationProcessedCorrectly(self, result):
        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], self.data["input"]["title"])
        self.assertEqual(entity["richDescription"], self.data["input"]["richDescription"])
        self.assertEqual(entity["startDate"], "2019-10-02T09:00:00+02:00")
        self.assertEqual(entity["endDate"], "2019-10-02T10:00:00+02:00")
        self.assertEqual(entity["maxAttendees"], self.data["input"]["maxAttendees"])
        self.assertEqual(entity["location"], self.data["input"]["location"])
        self.assertEqual(entity["locationLink"], self.data["input"]["locationLink"])
        self.assertEqual(entity["locationAddress"], self.data["input"]["locationAddress"])
        self.assertEqual(entity["source"], self.data["input"]["source"])
        self.assertEqual(entity["ticketLink"], self.data["input"]["ticketLink"])
        self.assertEqual(entity["attendEventWithoutAccount"], self.data["input"]["attendEventWithoutAccount"])
        self.assertEqual(entity["rsvp"], self.data["input"]["rsvp"])
        self.assertEqual(entity["qrAccess"], self.data["input"]["qrAccess"])
        self.assertEqual(entity["attendeeWelcomeMailSubject"], self.data["input"]["attendeeWelcomeMailSubject"])
        self.assertEqual(entity["attendeeWelcomeMailContent"], self.data["input"]["attendeeWelcomeMailContent"])
        self.assertDateEqual(entity['timePublished'], self.data["input"]["timePublished"])
        self.assertDateEqual(entity['scheduleArchiveEntity'], self.data["input"]["scheduleArchiveEntity"])
        self.assertDateEqual(entity['scheduleDeleteEntity'], self.data["input"]["scheduleDeleteEntity"])
        self.assertEqual(entity["slotsAvailable"][0]['name'], self.data["input"]["slotsAvailable"][0]['name'])
        self.assertEqual(entity['suggestedItems'], [{"guid": self.suggested_item.guid}])

    def test_edit_event_group_null_by_admin(self):
        variables = self.data
        variables["input"]["groupGuid"] = None

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["group"], None)

        self.eventPublic.refresh_from_db()
        self.assertEqual(entity["group"], None)

    def test_assign_subevent_to_slot(self):
        subevent: Event = EventFactory(parent=self.eventPublic)
        mutation = """
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        ... on Event {
                            guid
                            slotsAvailable {
                                name
                                subEventGuids
                            }
                        }
                    }
                }
            }
        """
        self.graphql_client.force_login(self.eventPublic.owner)

        # assign to slot
        self.graphql_client.post(mutation, {
            'input': {
                'guid': self.eventPublic.guid,
                'slotsAvailable': [
                    {
                        'name': "Some slot",
                        'subEventGuids': [subevent.guid]
                    },
                ],
            },
        })
        self.eventPublic.refresh_from_db()
        self.assertDictEqual({"content": [{"id": 0, "name": "Some slot"}]},
                             {"content": list(subevent.get_slots())})

        # Remove from slot
        self.graphql_client.post(mutation, {
            'input': {
                'guid': self.eventPublic.guid,
                'slotsAvailable': [],
            },
        })
        self.eventPublic.refresh_from_db()
        self.assertEqual([], [slot for slot in subevent.get_slots()])


class TestEditRangeEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.now = timezone.datetime.fromisoformat("2019-01-01T09:00:00+01:00")
        self.timezone_now = mock.patch("django.utils.timezone.now").start()
        self.timezone_now.return_value = self.now

        self.authenticated_user = mixer.blend(User)
        self.event = EventFactory(owner=self.authenticated_user,
                                  title="Initial title",
                                  start_date=self.now,
                                  end_date=self.now,
                                  range_starttime=self.now,
                                  range_settings={
                                      "type": "daily",
                                      "interval": 7
                                  })
        self.following_event = EventRangeFactory(self.event).create_next_event()

        self.variables = {
            'input': {
                "guid": self.event.guid,
                "title": "New title",
                "rangeSettings": {
                    "type": 'daily',
                    "interval": 7,
                    "updateRange": True,
                }
            },
        }
        self.mutation = """
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        ... on Event {
                            guid
                            title
                            rangeSettings {
                                repeatUntil
                                instanceLimit
                                type
                                interval
                                isIgnored
                                nextEvent {
                                    guid
                                    title
                                    rangeSettings {
                                        isIgnored
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

    def test_edit_range_event(self):
        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result['data']['editEntity']['entity']
        following = entity['rangeSettings']['nextEvent']

        self.assertEqual(entity['guid'], self.event.guid)
        self.assertEqual(entity['title'], 'New title')
        self.assertEqual(following['title'], 'New title')

    def test_edit_single_range_event(self):
        self.variables['input']['rangeSettings']['updateRange'] = False

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result['data']['editEntity']['entity']
        following = entity['rangeSettings']['nextEvent']

        self.assertEqual(entity['guid'], self.event.guid)
        self.assertEqual(entity['title'], 'New title')
        self.assertEqual(following['title'], 'Initial title')

        self.assertEqual(entity['rangeSettings']['isIgnored'], True)
        self.assertEqual(following['rangeSettings']['isIgnored'], False)

    def test_set_instance_limit_greater_then_number_of_items(self):
        changing_item = Event.objects.get_full_range(self.event).first()
        self.variables['input']['guid'] = changing_item.guid
        self.variables['input']['rangeSettings']['instanceLimit'] = 10
        self.assertEqual(Event.objects.count(), 2)

        self.graphql_client.force_login(self.event.owner)
        self.graphql_client.post(self.mutation, self.variables)
        self.assertTrue(Event.objects.count() > 1)

    def test_set_instance_limit_less_then_number_of_items(self):
        changing_item = Event.objects.get_full_range(self.event).first()
        self.variables['input']['guid'] = changing_item.guid
        self.variables['input']['rangeSettings']['instanceLimit'] = 1
        self.assertEqual(Event.objects.count(), 2)

        with self.assertGraphQlError("event_invalid_repeat_instance_limit"):
            self.graphql_client.force_login(self.event.owner)
            self.graphql_client.post(self.mutation, self.variables)

    def test_set_repeat_until_beyond_changing_items_date(self):
        changing_item = Event.objects.get_full_range(self.event).first()
        self.variables['input']['guid'] = changing_item.guid
        self.variables['input']['rangeSettings']['repeatUntil'] = (changing_item.start_date + timezone.timedelta(days=10)).isoformat()
        self.assertEqual(Event.objects.count(), 2)

        self.graphql_client.force_login(self.event.owner)
        self.graphql_client.post(self.mutation, self.variables)
        self.assertTrue(Event.objects.count() > 1)

    def test_set_repeat_until_less_then_changing_items_date(self):
        changing_item = Event.objects.get_full_range(self.event).first()
        self.variables['input']['guid'] = changing_item.guid
        self.variables['input']['rangeSettings']['repeatUntil'] = self.event.start_date.isoformat()
        self.assertEqual(Event.objects.count(), 2)

        with self.assertGraphQlError("event_invalid_repeat_until_date"):
            self.graphql_client.force_login(self.event.owner)
            self.graphql_client.post(self.mutation, self.variables)

    def test_change_interval_to_monthly(self):
        complete_range(self.event, timezone.now(), 10)
        changing_item = Event.objects.get_full_range(self.event)[4]
        earlier_before = [e.event.start_date for e in Event.objects.get_range_before(changing_item)]
        self_and_later_before = [changing_item.start_date] + [e.event.start_date for e in Event.objects.get_range_after(changing_item)]

        self.variables['input']['guid'] = changing_item.guid
        self.variables['input']['rangeSettings']['type'] = 'dayOfTheMonth'
        self.variables['input']['rangeSettings']['interval'] = 1

        self.graphql_client.force_login(self.event.owner)
        self.graphql_client.post(self.mutation, self.variables)

        earlier_after = [e.event.start_date for e in Event.objects.get_range_before(changing_item)]
        self_and_later_after = [changing_item.start_date] + [e.event.start_date for e in Event.objects.get_range_after(changing_item)]

        self.assertEqual(earlier_after, earlier_before)
        self.assertNotEqual(self_and_later_after, self_and_later_before)
