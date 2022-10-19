from django.urls import reverse
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from user.models import User
from event.models import Event, EventAttendee
from core.lib import generate_code


class TestCheckInEventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.eventOwner = mixer.blend(User)
        self.authenticatedUser = mixer.blend(User)
        self.event = mixer.blend(Event,
                                 owner=self.eventOwner
                                 )

        self.attendee1 = mixer.blend(EventAttendee,
                                     event=self.event,
                                     code=generate_code(),
                                     user=self.authenticatedUser
                                     )

    def tearDown(self):
        self.eventOwner.delete()
        self.authenticatedUser.delete()
        self.event.delete()
        self.attendee1.delete()
        super().tearDown()

    def test_check_in_by_owner(self):
        self.client.force_login(self.eventOwner)
        response = self.client.get(reverse("check_in") + '?code={}'.format(self.attendee1.code))

        self.assertEqual(response.status_code, 200)
