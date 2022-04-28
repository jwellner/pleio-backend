from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from user.models import User
from event.models import Event, EventAttendee
from django.http import HttpRequest, QueryDict
from core.lib import generate_code
from event.views import check_in

class TestCheckInEventTestCase(FastTenantTestCase):

    def setUp(self):
        self.eventOwner = mixer.blend(User)
        self.authenticatedUser = mixer.blend(User)
        self.event = mixer.blend(Event,
            owner=self.eventOwner
        )

        self.attendee1 = mixer.blend(EventAttendee, 
            event=self.event,
            code = generate_code(),
            user=self.authenticatedUser
        )

    def tearDown(self):
        self.eventOwner.delete()
        self.authenticatedUser.delete()
        self.event.delete()
        self.attendee1.delete()

    def test_check_in_by_owner(self):

        request = HttpRequest()
        request.user = self.eventOwner
        query = QueryDict('code={}'.format(self.attendee1.code))
        request.GET = query

        response = check_in(request)

        self.assertEqual(response.status_code, 200)