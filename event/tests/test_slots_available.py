from django.utils.timezone import localtime
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.tests.helpers import PleioTenantTestCase
from event.models import Event, EventSlot
from user.factories import UserFactory
from user.models import User


class TestSlotsAvailableTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner: User = UserFactory(email="owner@localhost")
        self.event: Event = mixer.blend(Event,
                                        title="Test event",
                                        owner=self.owner,
                                        start_date=localtime(),
                                        end_date=localtime(),
                                        write_access=[ACCESS_TYPE.user.format(self.owner.guid)],
                                        read_access=[ACCESS_TYPE.logged_in])

        self.primary_slot: EventSlot = EventSlot.objects.create(container=self.event, name="primary", index=0)
        self.secondary_slot: EventSlot = EventSlot.objects.create(container=self.event, name="secondary", index=1)

        self.mutation = """
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        ... on Event {
                            guid
                            slotsAvailable {
                                name
                            }
                        }
                    }
                }
            }
        """

    @staticmethod
    def buildInput(**kwargs):
        return {
            'input': kwargs
        }

    def test_reorder_slots_available(self):
        self.graphql_client.force_login(self.owner)
        response = self.graphql_client.post(self.mutation, self.buildInput(
            guid=self.event.guid,
            slotsAvailable=[{'id': self.secondary_slot.pk},
                            {'id': self.primary_slot.pk}]
        ))
        slots_available = response['data']['editEntity']['entity']['slotsAvailable']
        self.assertEqual([self.secondary_slot.name, self.primary_slot.name],
                         [s['name'] for s in slots_available])

    def test_add_available_slot(self):
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, self.buildInput(
            guid=self.event.guid,
            slotsAvailable=[
                {'id': self.primary_slot.pk},
                {'id': self.secondary_slot.pk},
                {'name': "New slot"},
            ]
        ))

        slots_available = result['data']['editEntity']['entity']['slotsAvailable']
        self.assertEqual(['primary', 'secondary', 'New slot'],
                         [s['name'] for s in slots_available])

    def test_rename_slot(self):
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, self.buildInput(
            guid=self.event.guid,
            slotsAvailable=[
                {'id': self.primary_slot.pk},
                {'id': self.secondary_slot.pk,
                 'name': 'Not secondary'},
            ]
        ))

        slots_available = result['data']['editEntity']['entity']['slotsAvailable']
        self.assertEqual(['primary', 'Not secondary'],
                         [s['name'] for s in slots_available])
