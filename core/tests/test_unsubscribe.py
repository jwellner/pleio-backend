from http import HTTPStatus
from unittest import mock

from core.tests.helpers import PleioTenantTestCase
from core.utils.mail import UnsubscribeTokenizer
from user.factories import UserFactory
from user.models import User


class TestUnsubscribeTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.recipient = self.create_recipient()
        self.unsubscribe_link = UnsubscribeTokenizer()

    def create_recipient(self) -> User:
        recipient = UserFactory()
        recipient.profile.receive_notification_email = True
        recipient.profile.overview_email_interval = 'weekly'
        recipient.profile.save()
        return recipient

    @mock.patch("core.views.UnsubscribeTokenizer.unpack")
    def test_expired_token(self, unpack):
        unpack.return_value = (self.recipient, UnsubscribeTokenizer.TYPE_OVERVIEW, True)

        url = self.unsubscribe_link.create_url(self.recipient, UnsubscribeTokenizer.TYPE_NOTIFICATIONS)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed("unsubscribe.html")

    @mock.patch("core.views.UnsubscribeTokenizer.unpack")
    @mock.patch("core.views.logger.error")
    def test_when_errors_occur(self, error_log, unpack):
        unpack.side_effect = Exception("Test with errors")

        url = self.unsubscribe_link.create_url(self.recipient, UnsubscribeTokenizer.TYPE_NOTIFICATIONS)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(error_log.call_count, 1)

    def test_unsubscribe_from_notifications(self):
        url = self.unsubscribe_link.create_url(self.recipient, UnsubscribeTokenizer.TYPE_NOTIFICATIONS)
        response = self.client.get(url)

        self.recipient.refresh_from_db()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertFalse(self.recipient.profile.receive_notification_email)
        self.assertEqual(self.recipient.profile.overview_email_interval, 'weekly')

    def test_unsubscribe_from_overview(self):
        url = self.unsubscribe_link.create_url(self.recipient, UnsubscribeTokenizer.TYPE_OVERVIEW)
        response = self.client.get(url)

        self.recipient.refresh_from_db()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(self.recipient.profile.receive_notification_email)
        self.assertEqual(self.recipient.profile.overview_email_interval, 'never')
