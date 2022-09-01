from unittest import mock

from django.test import override_settings
from faker import Faker
from mixer.backend.django import mixer
from notifications.signals import notify

from blog.models import Blog
from core import override_local_config
from core.factories import GroupFactory
from core.mail_builders.notifications import NotificationsMailer, serialize_notification
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestNotificationsMailerTestCase(PleioTenantTestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()

        self.author = UserFactory()
        self.recipient = UserFactory()
        self.mail_type = Faker().word()
        self.blog = mixer.blend(Blog, owner=self.author)
        self.clean_blog = mixer.blend(Blog, owner=self.author, title='')
        self.group = GroupFactory(owner=self.author)
        self.grouped_blog = mixer.blend(Blog, owner=self.author, title='', group=self.group)

        blog_notification, self.blog_notification = self.create_notification(self.blog)
        clean_notification, self.clean_notification = self.create_notification(self.clean_blog)
        group_notification, self.clean_grouped_notification = self.create_notification(self.grouped_blog)

        self.notifications = [self.blog_notification,
                              self.clean_notification,
                              self.clean_grouped_notification]

        self.mailer = NotificationsMailer(user=self.recipient.guid,
                                          notifications=[blog_notification.pk,
                                                         clean_notification.pk,
                                                         group_notification.pk],
                                          mail_type=self.mail_type)

    def create_notification(self, action_object, verb='created'):
        notification = notify.send(self.author, recipient=[self.recipient], verb=verb, action_object=action_object)[0][1][0]
        return notification, serialize_notification(notification)

    @override_local_config(EMAIL_NOTIFICATION_SHOW_EXCERPT=True)
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_mailer_context(self, mocked_build_context):
        mocked_build_context.return_value = {}
        self.mailer.notifications = self.notifications

        self.assertDictEqual(self.mailer.get_context(), {
            'mail_type': self.mail_type,
            'notifications': self.notifications,
            'show_excerpt': True,
        })
        self.assertEqual(mocked_build_context.called, True)
        self.assertEqual(mocked_build_context.call_args.kwargs['user'], self.recipient)

    @mock.patch("core.utils.mail.UnsubscribeTokenizer.create_url")
    @mock.patch("core.mail_builders.notifications.get_full_url")
    def test_mailer_headers(self, mocked_get_full_url, mocked_create_unsubscribe_url):
        mocked_create_unsubscribe_url.return_value = Faker().url()
        mocked_get_full_url.return_value = Faker().url()

        self.assertDictEqual(self.mailer.get_headers(), {
            'List-Unsubscribe': mocked_get_full_url.return_value
        })
        self.assertEqual(mocked_create_unsubscribe_url.called, True)
        self.assertEqual(mocked_create_unsubscribe_url.call_args.args,
                         (self.recipient, 'notifications'))
        self.assertEqual(mocked_get_full_url.called, True)
        self.assertEqual(mocked_get_full_url.call_args.args,
                         (mocked_create_unsubscribe_url.return_value,))

    @override_settings(LANGUAGE_CODE='en')
    @override_local_config(NAME="Testing Site")
    def test_mailer_subject(self):
        self.assertEqual(self.mailer.get_subject(), 'New notifications at Testing Site')

    @override_settings(LANGUAGE_CODE='en')
    def test_mailer_subject_one(self):
        self.mailer.notifications = [self.blog_notification]
        self.assertEqual(self.mailer.get_subject(), f'Notification on {self.blog.title}')

    @override_settings(LANGUAGE_CODE='en')
    def test_mailer_subject_one_notitle(self):
        self.mailer.notifications = [self.clean_notification]
        self.assertEqual(self.mailer.get_subject(), 'Notification on blog')

    @override_settings(LANGUAGE_CODE='en')
    def test_mailer_subject_one_grouped(self):
        self.mailer.notifications = [self.clean_grouped_notification]
        self.assertEqual(self.mailer.get_subject(), f'Notification on blog in group {self.group.name}')

    def test_mailer_properties(self):
        self.assertEqual(self.mailer.get_language(), self.recipient.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/send_notification_emails.html')
        self.assertEqual(self.mailer.get_receiver(), self.recipient)
        self.assertEqual(self.mailer.get_receiver_email(), self.recipient.email)
        self.assertEqual(self.mailer.get_sender(), None)
