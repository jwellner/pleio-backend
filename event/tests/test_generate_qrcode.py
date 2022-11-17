from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from event.models import Event
from core.views import get_url_qr
from user.models import User
from django.http import HttpRequest

from core.constances import USER_ROLES


class EventTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.eventPublic = mixer.blend(Event)

    def test_generate_qrcode(self):

        request = HttpRequest()
        request.user = self.authenticatedUser

        response = get_url_qr(request, self.eventPublic.id)

        self.assertEqual(response.status_code, 200)