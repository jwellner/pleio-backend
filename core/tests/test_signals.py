from django.db import connection
from django.test import TestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import User, Group, Comment
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from core.signals import comment_handler, user_handler, entity_handler
from django.utils.text import slugify
from django.db.models.signals import post_save
from unittest import mock


class SignalsTestCase(TestCase):

    def setUp(self):
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user1)
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
        self.comment1 = mixer.blend(Comment, is_closed=False, owner=self.user1, container=self.blog1)

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.group.delete()
        self.user1.delete()
        self.user2.delete()

    @mock.patch('notifications.signals.notify.send')
    def test_user_handler(self, mocked_send):
        user_handler(self.user1, self.user1, True)
        mocked_send.assert_called_once_with(self.user1, recipient=self.user1, verb="welcome")

    @mock.patch('notifications.signals.notify.send')
    def test_user_handler_not_created(self, mocked_send):
        user_handler(self.user1, self.user1, False)
        assert not mocked_send.called

    @mock.patch('notifications.signals.notify.send')
    def test_comment_handler(self, mocked_send):
        comment_handler(self.user1, self.comment1, True, action_object=self.blog1)
        mocked_send.assert_called_once()
        # TODO: how to mock queryset
        # mocked_send.assert_called_once_with(self.user1, recipient=self.user2, verb='commented', action_object=self.blog1)

    @mock.patch('notifications.signals.notify.send')
    def test_entitty_handler(self, mocked_send):
        entity_handler(self.user1, self.blog2, True, action_object=self.blog2)
        mocked_send.assert_called_once_with(self.user1, recipient=self.user2, verb='created', action_object=self.blog2)
