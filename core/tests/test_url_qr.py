from mixer.backend.django import mixer

from event.models import Event
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from core.constances import ACCESS_TYPE
from django.utils.text import slugify

class UrlQrTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.event = mixer.blend(Event, 
            owner = self.user1, 
            read_access=[ACCESS_TYPE.public])

    def test_url_qr_not_logged_in(self):
        response = self.client.get("/qr/url/{}".format(self.event.guid))
        self.assertEqual(response.status_code, 401)

    def test_url_qr(self):
        self.client.force_login(self.user1)
        response = self.client.get("/qr/url/{}".format(self.event.guid))

        self.assertEqual(response.headers['Content-Type'], 'image/png')
        self.assertIn(slugify(self.event.title), response.headers['Content-Disposition'])
        self.assertEqual(response.status_code, 200)