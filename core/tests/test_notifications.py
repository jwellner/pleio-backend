from django.db import connection
from django.test import TestCase
from core.models import User, Group, Comment
from blog.models import Blog
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer
from notifications.signals import notify


class NotificationsTestCase(TestCase):

    def setUp(self):
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.anonymousUser = AnonymousUser()
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

        self.query = """
            query NotificationsList($offset: Int) {
                notifications(offset: $offset, limit: 20) {
                    total
                    totalUnread
                    edges {
                    id
                    action
                    performer {
                        guid
                        name
                        username
                        icon
                        __typename
                    }
                    entity {
                        guid
                        ... on Blog {
                        title
                        url
                        __typename
                        }
                        ... on News {
                        title
                        url
                        __typename
                        }
                        ... on Discussion {
                        title
                        url
                        __typename
                        }
                        ... on Event {
                        title
                        url
                        __typename
                        }
                        ... on Question {
                        title
                        url
                        __typename
                        }
                        ... on Task {
                        title
                        url
                        __typename
                        }
                        ... on FileFolder {
                        title
                        url
                        __typename
                        }
                        ... on StatusUpdate {
                        url
                        __typename
                        }
                        ... on Wiki {
                        title
                        url
                        __typename
                        }
                        __typename
                    }
                    container {
                        guid
                        ... on Group {
                        name
                        __typename
                        }
                        __typename
                    }
                    isUnread
                    timeCreated
                    __typename
                    }
                    __typename
                }
            }

        """

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.group.delete()
        self.user2.delete()
        self.user1.delete()

    def test_notifications_without_action_object(self):
        """ use welcome message notification for test, is created at user creation, see core/signals.py"""

        request = HttpRequest()
        request.user = self.user1

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)
        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["notifications"]["edges"][0]["performer"]["guid"], str(self.user1.id))
        self.assertEqual(data["notifications"]["edges"][0]["container"], None)
        self.assertEqual(data["notifications"]["edges"][0]["entity"]["guid"], str(self.user1.id))

    def test_notifications_add_comment(self):
        request = HttpRequest()
        request.user = self.user2

        variables = {
        }
        comment1 = mixer.blend(Comment, is_closed=False, owner=self.user1, container=self.blog1)
        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]
        self.assertEqual(data["notifications"]["total"], 3)
        self.assertEqual(data["notifications"]["totalUnread"], 3)
        self.assertEqual(data["notifications"]["edges"][0]["performer"]["guid"], str(self.user1.id))
        self.assertEqual(data["notifications"]["edges"][0]["entity"]["guid"], str(self.blog1.id))
        self.assertEqual(data["notifications"]["edges"][0]["isUnread"], True)
        self.assertEqual(data["notifications"]["edges"][0]["action"], "commented")

    def test_notifications_content_to_group_added(self):
        request = HttpRequest()
        request.user = self.user2

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]
        self.assertEqual(data["notifications"]["total"], 2)
        self.assertEqual(data["notifications"]["totalUnread"], 2)
        self.assertEqual(data["notifications"]["edges"][0]["performer"]["guid"], str(self.user1.id))
        self.assertEqual(data["notifications"]["edges"][0]["entity"]["guid"], str(self.blog2.id))
        self.assertEqual(data["notifications"]["edges"][0]["isUnread"], True)
        self.assertEqual(data["notifications"]["edges"][0]["action"], "created")
        self.assertEqual(data["notifications"]["edges"][0]["action"], "created")

    def test_notifications_all_anonymous_user(self):
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value=request)
        self.assertTrue(result[0])
        data = result[1]["data"]
        self.assertEqual(data["notifications"]["total"], 0)
        self.assertEqual(data["notifications"]["totalUnread"], 0)
        self.assertEqual(data["notifications"]["edges"], list())
