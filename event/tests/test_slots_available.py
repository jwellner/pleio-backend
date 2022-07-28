from django.utils.timezone import localtime

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.models import Event
from user.factories import UserFactory
from user.models import User


def create_slot(name, *events):
    return {
        'name': name,
        'subEventGuids': [e.guid for e in events]
    }


class TestSlotsAvailableTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner: User = UserFactory(email="owner@localhost")
        self.event: Event = EventFactory(owner=self.owner,
                                         title="Test event",
                                         start_date=localtime())
        self.subevent1: Event = EventFactory(title='SubEvent1',
                                             start_date=localtime(),
                                             parent=self.event)
        self.subevent2: Event = EventFactory(title='SubEvent2',
                                             owner=self.owner,
                                             start_date=localtime(),
                                             parent=self.event)

        self.SLOTS_AVAILABLE = [
            create_slot("Slot 1", self.subevent1),
            create_slot("Slot 2", self.subevent1, self.subevent2),
        ]

        self.event.slots_available = self.SLOTS_AVAILABLE
        self.event.save()

        self.query = """
            query ($guid: String!) {
                entity(guid: $guid) {
                    ... on Event {
                        guid
                        slots
                        slotsAvailable {
                            name
                            subEventGuids
                        }
                    }
                }
            }
        """

    def test_slots_available(self):
        self.graphql_client.force_login(self.owner)

        response = self.graphql_client.post(self.query, {'guid': self.event.guid})
        entity = response['data']['entity']
        self.assertEqual(entity['guid'], self.event.guid)
        self.assertEqual(entity['slots'], [])
        self.assertDictEqual({'content': self.SLOTS_AVAILABLE},
                             {'content': entity['slotsAvailable']})

        response = self.graphql_client.post(self.query, {'guid': self.subevent1.guid})
        entity = response['data']['entity']
        self.assertEqual(entity['guid'], self.subevent1.guid)
        self.assertEqual(entity['slots'], ["Slot 1", "Slot 2"])
        self.assertEqual(entity['slotsAvailable'], [])

        response = self.graphql_client.post(self.query, {'guid': self.subevent2.guid})
        entity = response['data']['entity']
        self.assertEqual(entity['guid'], self.subevent2.guid)
        self.assertEqual(entity['slots'], ["Slot 2"])
        self.assertEqual(entity['slotsAvailable'], [])
