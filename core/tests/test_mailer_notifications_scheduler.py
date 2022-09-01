from unittest import mock

from mixer.backend.django import mixer
from notifications.signals import notify

from blog.models import Blog
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestNotificationMailerSchedulerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.author = UserFactory()
        self.recipient = UserFactory()

        self.blog = mixer.blend(Blog, author=self.author)
        self.notifications = [r[1][0] for r in notify.send(self.author, recipient=[self.recipient], verb='created', action_object=self.blog)]

    @mock.patch("core.models.mail.MailInstanceManager.submit")
    def test_scheduler_args(self, mocked_submit):
        from core.mail_builders.notifications import send_notifications, MailTypeEnum, NotificationsMailer

        send_notifications(self.recipient, self.notifications, MailTypeEnum.COLLECTED)

        self.assertEqual(mocked_submit.call_args.args[0], NotificationsMailer)
        self.assertDictEqual(mocked_submit.call_args.args[1], {
            "user": self.recipient.guid,
            "notifications": [self.notifications[0].id],
            "mail_type": MailTypeEnum.COLLECTED
        })

