from django_tenants.test.cases import FastTenantTestCase
from core.models import Group, Comment
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


class SendNotificationEmailsTestCase(FastTenantTestCase):

    def setUp(self):
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user1, auto_notification=True)
        self.group.join(self.user2, 'member')
        self.blog1 = Blog.objects.create(
            title='Blog1',
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.follow1 = self.blog1.add_follow(self.user2)

    def tearDown(self):
        self.blog1.delete()

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_command_send_5_notifications(self, mocked_send_mail_multi):
        comments = mixer.cycle(5).blend(Comment, is_closed=False, owner=self.user1, container=self.blog1)
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
        assert not mocked_send_mail_multi.called

    def test_notifications_marked_as_sent(self):
        comments = mixer.cycle(10).blend(Comment, is_closed=False, owner=self.user1, container=self.blog1)
        call_command('send_notification_emails')

        self.assertEqual(len(self.user2.notifications.filter(emailed=False)), 0)

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_notifications_not_sent_to_banned_users(self, mocked_send_mail_multi):
        comment1 = mixer.blend(Comment, is_closed=False, owner=self.user1, container=self.blog1)
        self.user2.is_active = False
        self.user2.save()
        call_command('send_notification_emails')
        assert not mocked_send_mail_multi.called

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_notifications_not_sent_to_users_with_last_login_more_6_months_ago(self, mocked_send_mail_multi):
        comment1 = mixer.blend(Comment, is_closed=False, owner=self.user1, container=self.blog1)
        nr_months_ago_6 = datetime.now() - timedelta(hours=4464)
        self.user2.profile.last_online = nr_months_ago_6
        self.user2.profile.save()
        self.user2.save()
        call_command('send_notification_emails')
        assert not mocked_send_mail_multi.called

    @mock.patch('core.management.commands.send_notification_emails.send_mail_multi.delay')
    def test_template_context_of_commented_notification(self, mocked_send_mail_multi):
        comment1 = mixer.blend(Comment, is_closed=False, owner=self.user1, container=self.blog1)
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
