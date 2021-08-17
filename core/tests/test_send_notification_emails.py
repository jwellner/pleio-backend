from django_tenants.test.cases import FastTenantTestCase
from django.db import connection
from core.models import Group, Comment
from core.tasks import create_notification
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from django.http import HttpRequest
from mixer.backend.django import mixer
from notifications.signals import notify
from django.core.management import call_command
from io import StringIO
from unittest import mock
from core import config
from datetime import datetime, timedelta
from contextlib import contextmanager


class SendNotificationEmailsTestCase(FastTenantTestCase):

    def setUp(self):
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

    def tearDown(self):
        self.blog1.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.group.delete()

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_command_send_5_notifications(self, mocked_send_mail_multi):
        i = 0
        while i < 5:
            notify.send(self.user1, recipient=[self.user2], verb="created", action_object=self.blog1)[0][1]
            i += 1

        call_command('send_notification_emails')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = "Nieuwe notificaties op %s" % config.NAME

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[0], 'fast_test')
        self.assertEqual(args[1], subject)
        self.assertEqual(args[2], 'email/send_notification_emails.html')
        self.assertEqual(len(args[3]['notifications']), 5)
        self.assertEqual(args[4], self.user2.email)

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_command_do_not_send_welcome_notification(self, mocked_send_mail_multi):
        """ Welcome notification is created on user creation, this should not be send """
        call_command('send_notification_emails')
        self.assertEqual(mocked_send_mail_multi.call_count, 0)

    def test_notifications_marked_as_sent(self):
        i = 0
        while i < 10:
            notify.send(self.user1, recipient=[self.user2], verb="created", action_object=self.blog1)[0][1]
            i = i + 1
        call_command('send_notification_emails')

        self.assertEqual(len(self.user2.notifications.filter(emailed=False)), 0)

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_notifications_not_sent_to_banned_users(self, mocked_send_mail_multi):
        create_notification.s(connection.schema_name, 'commented', self.blog1.id, self.user1.id).apply()
        self.user2.is_active = False
        self.user2.save()
        call_command('send_notification_emails')
        self.assertEqual(mocked_send_mail_multi.call_count, 0)

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_notifications_not_sent_notifications_off(self, mocked_send_mail_multi):
        create_notification.s(connection.schema_name, 'commented', self.blog1.id, self.user1.id).apply()
        self.user2.profile.receive_notification_email = False
        self.user2.profile.save()
        self.user2.is_active = True
        self.user2.save()
        call_command('send_notification_emails')
        self.assertEqual(mocked_send_mail_multi.call_count, 0)

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_template_context_of_commented_notification(self, mocked_send_mail_multi):
        create_notification.s(connection.schema_name, 'commented', self.blog1.id, self.user1.id).apply()
        call_command('send_notification_emails')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = "Nieuwe notificaties op %s" % config.NAME

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[3]['notifications'][0]['action'], 'commented')
        self.assertEqual(args[3]['notifications'][0]['performer_name'], self.user1.name)
        self.assertEqual(args[3]['notifications'][0]['entity_title'], self.blog1.title)
        self.assertEqual(args[3]['notifications'][0]['entity_group_name'], "")
        self.assertEqual(args[3]['notifications'][0]['isUnread'], True)

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_template_context_of_created_notification(self, mocked_send_mail_multi):
        blog2 = Blog.objects.create(
            title='Blog2',
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group
        )
        create_notification.s(connection.schema_name, 'created', blog2.id, self.user1.id).apply()

        call_command('send_notification_emails')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = "Nieuwe notificaties op %s" % config.NAME

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[3]['notifications'][0]['action'], 'created')
        self.assertEqual(args[3]['notifications'][0]['performer_name'], self.user1.name)
        self.assertEqual(args[3]['notifications'][0]['entity_title'], blog2.title)
        self.assertEqual(args[3]['notifications'][0]['entity_description'], blog2.description)
        self.assertEqual(args[3]['notifications'][0]['entity_url'], blog2.url)
        self.assertEqual(args[3]['notifications'][0]['entity_group'], True)
        self.assertEqual(args[3]['notifications'][0]['entity_group_name'], self.group.name)
        self.assertEqual(args[3]['notifications'][0]['entity_group_url'], self.group.url)
        self.assertEqual(args[3]['notifications'][0]['type_to_string'], blog2.type_to_string)
        self.assertEqual(args[3]['notifications'][0]['isUnread'], True)

        blog2.delete()

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_command_notifications_disabled(self, mocked_send_mail_multi):
        i = 0
        while i < 5:
            create_notification.s(connection.schema_name, 'created', self.blog1.id, self.user1.id).apply()
            i = i + 1

        call_command('send_notification_emails')

        self.assertEqual(mocked_send_mail_multi.call_count, 0)
