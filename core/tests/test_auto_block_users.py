from django.db import connection
from django.test import override_settings
from django.utils.translation import gettext
from mixer.backend.django import mixer
from django.core.cache import cache

from tenants.helpers import FastTenantTestCase
from user.models import User
from unittest import mock
from core.tasks import ban_users_that_bounce, ban_users_with_no_account


class AutoBlockUsersTests(FastTenantTestCase):
    def setUp(self):
        super().setUp()
        cache.set("%s%s" % (connection.schema_name, 'LAST_RECEIVED_BOUNCING_EMAIL'), '2000-01-01')

        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User, external_id=233)
        self.user4 = mixer.blend(User, external_id=235)

    def tearDown(self):
        cache.clear()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.user4.delete()
        super().tearDown()

    @override_settings(BOUNCER_URL='domain@url.nl')
    @override_settings(BOUNCER_TOKEN='fake_token')
    @mock.patch('requests.get')
    def test_auto_block_bounced_email(self, mocked_get):

        json_data =  [
            {
                "email": self.user2.email,
                "last_received": "2019-11-12T21:04:04.164410Z",
                "count": 1
            },
            {
                "email": self.user4.email,
                "last_received": "2019-11-12T21:04:11.664173Z",
                "count": 3
            },
            {
                "email": "test@test.nl",
                "last_received": "2019-11-12T21:04:11.664173Z",
                "count": 3
            }
        ]


        mocked_get.return_value.json.return_value = json_data
        
        task = ban_users_that_bounce.s(connection.schema_name).apply()

        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.user3.refresh_from_db()
        self.user4.refresh_from_db()

        self.assertEqual(self.user1.is_active, True)
        self.assertEqual(self.user1.ban_reason, '')
        self.assertEqual(self.user2.is_active, False)
        self.assertEqual(self.user2.ban_reason, gettext('Bouncing e-mail address'))
        self.assertEqual(self.user3.is_active, True)
        self.assertEqual(self.user4.is_active, False)
        self.assertEqual(self.user4.ban_reason, gettext('Bouncing e-mail address'))

    @override_settings(ACCOUNT_API_URL='domain@url.nl')
    @override_settings(ACCOUNT_API_TOKEN='fake_token')
    @mock.patch('requests.get')
    def test_auto_block_deleted_user_account(self, mocked_get):

        json_data =  [
            {
                "userid": self.user3.external_id,
                "event_time": "2019-02-04T09:18:38.361726Z",
                "event_type": "ACCOUNT_DELETED"
            },
            {
                "userid": self.user4.external_id,
                "event_time": "2019-04-10T13:02:02.339155Z",
                "event_type": "ACCOUNT_DELETED"
            },
            {
                "userid": 326,
                "event_time": "2020-05-19T11:45:34.010968Z",
                "event_type": "ACCOUNT_DELETED"
            }
        ]


        mocked_get.return_value.json.return_value = json_data
        
        task = ban_users_with_no_account.s(connection.schema_name).apply()

        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.user3.refresh_from_db()
        self.user4.refresh_from_db()

        self.assertEqual(self.user1.is_active, True)
        self.assertEqual(self.user1.ban_reason, '')
        self.assertEqual(self.user2.is_active, True)
        self.assertEqual(self.user3.is_active, False)
        self.assertEqual(self.user3.ban_reason, gettext('User deleted externally'))
        self.assertEqual(self.user4.is_active, False)
        self.assertEqual(self.user4.ban_reason, gettext('User deleted externally'))
