from django_tenants.test.cases import FastTenantTestCase
from core.models import Group, Comment, Setting, EntityView
from user.models import User
from blog.models import Blog
from news.models import News
from core.constances import ACCESS_TYPE
from django.utils.translation import ugettext_lazy
from django.http import HttpRequest
from django.core.cache import cache
from mixer.backend.django import mixer
from notifications.signals import notify
from django.core.management import call_command
from io import StringIO
from unittest import mock
from core import config
from django.db import connection
from datetime import datetime, timedelta


class SendOverviewEmailsTestCase(FastTenantTestCase):

    def setUp(self):
        self.user1 = mixer.blend(User, is_active=False)
        self.user2 = mixer.blend(User)
        self.user2.profile.overview_email_tags = ['tagged']
        self.user2.profile.save()

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()

    @mock.patch('core.management.commands.send_overview_emails.send_mail_multi')
    def test_command_send_overview_5_entities(self, mocked_send_mail_multi):

        blogs = mixer.cycle(3).blend(
            Blog,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        news = mixer.cycle(3).blend(
            News,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        call_command('send_overview_emails', url='http://test.test', interval='weekly')

        args, kwargs = mocked_send_mail_multi.call_args

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[0], "Regular overview of %s" % config.NAME)
        self.assertEqual(args[1], 'email/send_overview_emails.html')
        self.assertEqual(len(args[2]['entities']), 5)
        self.assertEqual(args[2]['intro_text'], '')
        self.assertEqual(args[2]['title'], 'Pleio 2.0')
        self.assertEqual(args[3], [self.user2.email])

    @mock.patch('core.management.commands.send_overview_emails.send_mail_multi')
    def test_command_send_overview_do_not_send_entities_twice(self, mocked_send_mail_multi):

        blogs = mixer.cycle(3).blend(
            Blog,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        news = mixer.cycle(3).blend(
            News,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        call_command('send_overview_emails', url='http://test.test', interval='weekly')
        call_command('send_overview_emails', url='http://test.test', interval='weekly')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = ugettext_lazy("Regular overview of %s" % config.NAME)

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[0], subject)
        self.assertEqual(args[1], 'email/send_overview_emails.html')
        self.assertEqual(len(args[2]['entities']), 5)
        self.assertEqual(args[3], [self.user2.email])


    @mock.patch('core.management.commands.send_overview_emails.send_mail_multi')
    def test_command_send_overview_to_users_with_daily_monthly_interval(self, mocked_send_mail_multi):

        user3 = mixer.blend(User)
        user3.profile.overview_email_interval = 'daily'
        user3.profile.save()

        user4 = mixer.blend(User)
        user4.profile.overview_email_interval = 'monthly'
        user4.profile.save()

        blogs = mixer.cycle(3).blend(
            Blog,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        news = mixer.cycle(3).blend(
            News,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        call_command('send_overview_emails', url='http://test.test', interval='daily')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = ugettext_lazy("Regular overview of %s" % config.NAME)

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[0], subject)
        self.assertEqual(args[1], 'email/send_overview_emails.html')
        self.assertEqual(len(args[2]['entities']), 5)
        self.assertEqual(args[3], [user3.email])

        call_command('send_overview_emails', url='http://test.test', interval='monthly')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = ugettext_lazy("Regular overview of %s" % config.NAME)

        self.assertEqual(mocked_send_mail_multi.call_count, 2)
        self.assertEqual(args[0], subject)
        self.assertEqual(args[1], 'email/send_overview_emails.html')
        self.assertEqual(len(args[2]['entities']), 5)
        self.assertEqual(args[3], [user4.email])

        user3.delete()
        user4.delete()


    @mock.patch('core.management.commands.send_overview_emails.send_mail_multi')
    def test_command_send_overview_default_email_frequency(self, mocked_send_mail_multi):

        cache.set("%s%s" % (connection.schema_name, 'EMAIL_OVERVIEW_DEFAULT_FREQUENCY'), 'daily')
        cache.set("%s%s" % (connection.schema_name, 'EMAIL_OVERVIEW_SUBJECT'), 'test other subject')
        cache.set("%s%s" % (connection.schema_name, 'EMAIL_OVERVIEW_TITLE'), 'title text')
        cache.set("%s%s" % (connection.schema_name, 'EMAIL_OVERVIEW_INTRO'), 'introduction text')

        blogs = mixer.cycle(3).blend(
            Blog,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        news = mixer.cycle(3).blend(
            News,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        call_command('send_overview_emails', url='http://test.test', interval='daily')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = ugettext_lazy("Regular overview of %s" % config.NAME)

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[0], 'test other subject')
        self.assertEqual(args[1], 'email/send_overview_emails.html')
        self.assertEqual(len(args[2]['entities']), 5)
        self.assertEqual(args[2]['intro_text'], 'introduction text')
        self.assertEqual(args[2]['title'], 'title text')
        self.assertEqual(args[3], [self.user2.email])

        cache.clear()


    @mock.patch('core.management.commands.send_overview_emails.send_mail_multi')
    def test_command_send_overview_5_entities_one_featured(self, mocked_send_mail_multi):

        mixer.cycle(3).blend(
            Blog,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        featuredBlog = Blog.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            is_recommended=True
        )

        mixer.cycle(3).blend(
            Blog,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        call_command('send_overview_emails', url='http://test.test', interval='weekly')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = ugettext_lazy("Regular overview of %s" % config.NAME)

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[0], subject)
        self.assertEqual(args[1], 'email/send_overview_emails.html')
        self.assertEqual(len(args[2]['entities']), 5)
        self.assertNotIn(featuredBlog.guid, [d.guid for d in args[2]['entities']])
        self.assertEqual(len(args[2]['featured']), 1)
        self.assertEqual(args[2]['featured'][0].guid, featuredBlog.guid)
        self.assertEqual(args[3], [self.user2.email])


    @mock.patch('core.management.commands.send_overview_emails.send_mail_multi')
    def test_command_not_send_viewed_entities(self, mocked_send_mail_multi):

        featuredBlog1 = Blog.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            is_recommended=True
        )

        featuredBlog2 = Blog.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            is_recommended=True
        )

        blog1 = Blog.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        blog2 = Blog.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        EntityView.objects.create(entity=blog1, viewer=self.user2)
        EntityView.objects.create(entity=featuredBlog1, viewer=self.user2)

        call_command('send_overview_emails', url='http://test.test', interval='weekly')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = ugettext_lazy("Regular overview of %s" % config.NAME)

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[0], subject)
        self.assertEqual(args[1], 'email/send_overview_emails.html')
        self.assertEqual(len(args[2]['entities']), 1)
        self.assertEqual(args[2]['entities'][0].guid, blog2.guid)
        # viewed featured entities are sent, also if already viewed
        self.assertEqual(len(args[2]['featured']), 2)
        self.assertEqual(args[3], [self.user2.email])


    @mock.patch('core.management.commands.send_overview_emails.send_mail_multi')
    def test_command_send_overview_5_entities_with_tag_preference(self, mocked_send_mail_multi):

        blogs = mixer.cycle(6).blend(
            Blog,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        blog1 = Blog.objects.create(
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            tags=['tagged']
        )

        news = mixer.cycle(3).blend(
            News,
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

        call_command('send_overview_emails', url='http://test.test', interval='weekly')

        args, kwargs = mocked_send_mail_multi.call_args
        subject = ugettext_lazy("Regular overview of %s" % config.NAME)

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
        self.assertEqual(args[0], subject)
        self.assertEqual(args[1], 'email/send_overview_emails.html')
        self.assertEqual(len(args[2]['entities']), 5)
        self.assertEqual(args[2]['entities'][0].guid, blog1.guid)
        self.assertEqual(args[3], [self.user2.email])