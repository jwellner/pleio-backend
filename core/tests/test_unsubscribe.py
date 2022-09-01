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

    def test_unsubscribe_from_notifications(self):
        url = self.unsubscribe_link.create_url(self.recipient, UnsubscribeTokenizer.TYPE_NOTIFICATIONS)
        response = self.client.get(url)

        self.recipient.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.recipient.profile.receive_notification_email)
        self.assertEqual(self.recipient.profile.overview_email_interval, 'weekly')

    def test_unsubscribe_from_overview(self):
        url = self.unsubscribe_link.create_url(self.recipient, UnsubscribeTokenizer.TYPE_OVERVIEW)
        response = self.client.get(url)

        self.recipient.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.recipient.profile.receive_notification_email)
        self.assertEqual(self.recipient.profile.overview_email_interval, 'never')
