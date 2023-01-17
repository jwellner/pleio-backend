import uuid
from http import HTTPStatus

from django.urls import reverse

from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestViewsAvatarTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory(external_id=1)
        self.override_config(IS_CLOSED=False)
        self.override_setting(PROFILE_PICTURE_URL="https://account.pleio.nl")

    def tearDown(self):
        self.user.delete()
        super().tearDown()

    def test_avatar(self):
        response = self.client.get(reverse('avatar', args=[self.user.guid]), data={
            'size': 200,
        })

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, f"https://account.pleio.nl/avatar/{self.user.email}/200/")

    def test_avatar_invalid_user(self):
        self.user.external_id = None
        self.user.save()

        response = self.client.get(reverse('avatar', args=[self.user.guid]), data={
            'size': 200,
        })

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_avatar_not_existing_user(self):
        response = self.client.get(reverse('avatar', args=[uuid.uuid4()]), data={
            'size': 200,
        })

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
