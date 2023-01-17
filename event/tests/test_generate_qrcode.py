import uuid

from django.contrib.auth.models import AnonymousUser
from mixer.backend.django import mixer

from core.http import UnauthorizedReact, NotFoundReact
from event.models import Event
from core.views import get_url_qr
from tenants.helpers import FastTenantTestCase
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

    def test_generate_qrcode_non_entity(self):
        random_id = uuid.uuid4()
        request = HttpRequest()
        request.user = self.authenticatedUser

        with self.assertRaises(NotFoundReact):
            get_url_qr(request, str(random_id))

    def test_generate_qrcode_not_logged_in(self):
        request = HttpRequest()
        request.user = AnonymousUser()

        with self.assertRaises(UnauthorizedReact):
            get_url_qr(request, self.eventPublic.id)
