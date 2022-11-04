from tenants.helpers import FastTenantTestCase
from user.factories import UserFactory
from unittest import mock


class TestNewUserTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = UserFactory()

    @mock.patch('notifications.signals.notify.send')
    def test_notification_send(self, mocked_send):
        self.tmp = UserFactory()
        mocked_send.assert_called_once_with(self.tmp, recipient=self.tmp, verb="welcome", action_object=self.tmp)
        self.tmp.delete()

    @mock.patch('notifications.signals.notify.send')
    def test_notification_not_send(self, mocked_send):
        self.user1.name = "Test 123"
        assert not mocked_send.called
