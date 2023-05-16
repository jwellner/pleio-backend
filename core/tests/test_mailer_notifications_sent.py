import random
from django.core.management import call_command
from django.db import connection

from core.mail_builders.notifications import MailTypeEnum
from core.models import Group
from core.tasks import create_notification
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from notifications.signals import notify
from unittest import mock


class SendNotificationEmailsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user2.profile.receive_notification_email = True
        self.user2.profile.save()
        self.user3 = mixer.blend(User)
        self.user3.profile.receive_notification_email = False
        self.user3.profile.save()
        self.group = mixer.blend(Group, owner=self.user1, auto_notification=True)
        self.group.join(self.user2, 'member')
        self.group.join(self.user3, 'member')

        self.group_user2 = mixer.blend(Group, owner=self.user1, auto_notification=True)
        self.group_user2.join(self.user2, 'member')

        self.blog1 = Blog.objects.create(
            title='Blog1',
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        self.blog2 = Blog.objects.create(
            title='Blog1',
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        self.follow1 = self.blog1.add_follow(self.user2)
        self.follow2 = self.blog1.add_follow(self.user3)
        self.verbs = ["created", "mentioned", "commented"]

    def tearDown(self):
        super().tearDown()

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_command_do_not_send_welcome_notification(self, mocked_send_notifications):
        """ Welcome notification is created on user creation, this should not be send """
        call_command('send_notification_emails')
        self.assertEqual(mocked_send_notifications.call_count, 0)

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_command_send_5_notifications(self, mocked_send_notifications):
        i = 0
        while i < 5:
            notify.send(self.user1, recipient=[self.user2], verb=random.choice(self.verbs), action_object=self.blog1)
            i += 1

        call_command('send_notification_emails')

        args, kwargs = mocked_send_notifications.call_args
        self.assertEqual(args[0], self.user2)
        self.assertEqual([notification.action_object for notification in args[1]],
                         [self.blog1, self.blog1, self.blog1, self.blog1, self.blog1])
        self.assertEqual(args[2], MailTypeEnum.COLLECTED)

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notifications_marked_as_sent(self, mocked_send_notifications):
        i = 0
        while i < 10:
            notify.send(self.user1, recipient=[self.user2], verb=random.choice(self.verbs), action_object=self.blog1)
            i = i + 1
        call_command('send_notification_emails')

        self.assertEqual(mocked_send_notifications.call_count, 1)
        self.assertEqual(len(self.user2.notifications.filter(emailed=False, verb__in=['created', 'commented', 'mentioned'])), 0)

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notifications_not_sent_to_banned_users(self, mocked_send_notifications):
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog1.id, self.user1.id).apply()
        self.user2.is_active = False
        self.user2.save()
        call_command('send_notification_emails')
        self.assertEqual(mocked_send_notifications.call_count, 0)

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notifications_not_sent_notifications_off(self, mocked_send_notifications):
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog1.id, self.user1.id).apply()
        self.user2.profile.receive_notification_email = False
        self.user2.profile.save()
        self.user2.is_active = True
        self.user2.save()
        call_command('send_notification_emails')
        self.assertEqual(mocked_send_notifications.call_count, 0)

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_template_context_of_created_notification(self, mocked_send_notifications):
        blog2 = Blog.objects.create(
            title='Blog2',
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group
        )
        create_notification.s(connection.schema_name, 'created', 'blog.blog', blog2.id, self.user1.id).apply()

        call_command('send_notification_emails')

        self.assertEqual(mocked_send_notifications.call_count, 1)

        args, kwargs = mocked_send_notifications.call_args
        self.assertEqual(args[0], self.user2)
        self.assertEqual(args[1][0].action_object, blog2)
        self.assertEqual(args[2], MailTypeEnum.COLLECTED)

        blog2.delete()

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_command_notifications_disabled(self, mocked_send_notifications):
        i = 0
        while i < 5:
            create_notification.s(connection.schema_name, 'created', 'blog.blog', self.blog1.id, self.user1.id).apply()
            i = i + 1

        call_command('send_notification_emails')

        self.assertEqual(mocked_send_notifications.call_count, 0)
