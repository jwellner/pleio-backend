from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Comment
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from core.signals import comment_handler, mention_handler, notification_handler, user_handler
from core.tests.helpers import QuerySetWith
from django.utils.text import slugify
from django.db.models.signals import post_save
from notifications.models import Notification
from unittest import mock


class SignalsTestCase(FastTenantTestCase):

    def setUp(self):
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user1, auto_notification=True)
        self.group.join(self.user2, 'member')
        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group
        )
        self.follow1 = self.blog1.add_follow(self.user2)
        self.comment1 = Comment.objects.create(
            owner=self.user1,
            container=self.blog1
        )

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.group.delete()
        self.user1.delete()
        self.user2.delete()

    @mock.patch('notifications.signals.notify.send')
    def test_user_handler(self, mocked_send):
        user_handler(self.user1, self.user1, True)
        mocked_send.assert_called_once_with(self.user1, recipient=self.user1, verb="welcome", action_object=self.user1)

    @mock.patch('notifications.signals.notify.send')
    def test_user_handler_not_created(self, mocked_send):
        user_handler(self.user1, self.user1, False)
        assert not mocked_send.called

    @mock.patch('core.tasks.create_notification.delay')
    def test_comment_handler(self, mocked_create_notification):
        comment_handler(self.user1, self.comment1, True, action_object=self.blog1)
        mocked_create_notification.has_calls([
            mock.call(connection.schema_name, 'commented', 'blog.blog', self.blog1.id, self.comment1.owner.id),
            mock.call(connection.schema_name, 'mentioned', 'blog.blog', self.comment1.id, self.comment1.owner.id),

        ])

    @mock.patch('core.tasks.create_notification.delay')
    def test_notification_handler(self, mocked_create_notification):
        notification_handler(self.user1, self.blog2, True, action_object=self.blog2)
        mocked_create_notification.has_calls([
            mock.call(connection.schema_name, 'created', 'blog.blog', self.blog2.id, self.blog2.owner.id),
            mock.call(connection.schema_name, 'mentioned', 'blog.blog', self.blog2.id, self.blog2.owner.id),
        ])

    @mock.patch('core.tasks.create_notification.delay')
    def test_mention_handler(self, mocked_create_notification):
        mentionObj = Blog(owner=self.user1)

        mention_handler(self.user1, mentionObj, True)
        mocked_create_notification.assert_called_once_with(connection.schema_name, 'mentioned', 'blog.blog', mentionObj.id, self.user1.id)
