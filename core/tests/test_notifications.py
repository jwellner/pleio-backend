from django.db import connection
from core.models import Group, Comment
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from core.tasks import create_notification
from django.db.models.signals import post_save
from mixer.backend.django import mixer

import functools
from django.dispatch import receiver


def suspendingreceiver(signal, **decorator_kwargs):
    def our_wrapper(func):
        @receiver(signal, **decorator_kwargs)
        @functools.wraps(func)
        def fake_receiver(sender, **kwargs):
            return

        return fake_receiver

    return our_wrapper


class NotificationsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
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
        self.comment1 = Comment.objects.create(
            owner=self.user1,
            container=self.blog1
        )

        self.query = """
            query NotificationsList($offset: Int, $unread: Boolean) {
                notifications(offset: $offset, limit: 20, unread: $unread) {
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
                    }
                    entity {
                        guid
                        ... on Blog {
                        title
                        url
                        }
                        ... on News {
                        title
                        url
                        }
                        ... on Discussion {
                        title
                        url
                        }
                        ... on Event {
                        title
                        url
                        }
                        ... on Question {
                        title
                        url
                        }
                        ... on Task {
                        title
                        url
                        }
                        ... on File {
                        title
                        url
                        }
                        ... on Folder {
                        title
                        url
                        }
                        ... on StatusUpdate {
                        url
                        }
                        ... on Wiki {
                        title
                        url
                        }
                    }
                    container {
                        guid
                        ... on Group {
                        name
                        }
                    }
                    isUnread
                    timeCreated
                    }
                }
            }

        """

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.group.delete()
        self.user2.delete()
        self.user1.delete()
        super().tearDown()

    def test_notifications_without_action_object(self):
        """ use welcome message notification for test, is created at user creation, see core/signals.py"""
        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["notifications"]["edges"][0]["performer"]["guid"], str(self.user1.id))
        self.assertEqual(data["notifications"]["edges"][0]["container"], None)
        self.assertEqual(data["notifications"]["edges"][0]["entity"]["guid"], str(self.user1.id))

    @suspendingreceiver(post_save, sender=Comment)
    def test_notifications_add_comment(self):
        i = 0
        while i < 10:
            create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.comment1.container.id, self.comment1.owner.id).apply()
            i = i + 1

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["notifications"]["total"], 11)
        self.assertEqual(data["notifications"]["totalUnread"], 11)
        self.assertEqual(data["notifications"]["edges"][0]["performer"]["guid"], str(self.user1.id))
        self.assertEqual(data["notifications"]["edges"][0]["entity"]["guid"], str(self.blog1.id))
        self.assertEqual(data["notifications"]["edges"][0]["isUnread"], True)
        self.assertEqual(data["notifications"]["edges"][0]["action"], "commented")

    @suspendingreceiver(post_save, sender=Comment)
    def test_notifications_unread_filter(self):
        variables = {
            "unread": True
        }
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.comment1.container.id, self.comment1.owner.id).apply()
        notification = self.user2.notifications.all()[0]
        notification.mark_as_read()

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["notifications"]["total"], 1)
        self.assertEqual(data["notifications"]["totalUnread"], 1)

        variables = {
            "unread": False
        }
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["notifications"]["total"], 1)
        self.assertEqual(data["notifications"]["totalUnread"], 1)

    @suspendingreceiver(post_save, sender=Blog)
    def test_notifications_content_to_group_added(self):
        create_notification.s(connection.schema_name, 'created', 'blog.blog', self.blog2.id, self.user1.id).apply()

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["notifications"]["total"], 2)
        self.assertEqual(data["notifications"]["totalUnread"], 2)

        self.assertEqual(data["notifications"]["edges"][0]["performer"]["guid"], str(self.user1.id))
        self.assertEqual(data["notifications"]["edges"][0]["entity"]["guid"], str(self.blog2.id))
        self.assertEqual(data["notifications"]["edges"][0]["isUnread"], True)
        self.assertEqual(data["notifications"]["edges"][0]["action"], "created")

    def test_notifications_all_anonymous_user(self):
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["notifications"]["total"], 0)
        self.assertEqual(data["notifications"]["totalUnread"], 0)
        self.assertEqual(data["notifications"]["edges"], list())

    @suspendingreceiver(post_save, sender=Blog)
    def test_notifications_content_deleted(self):
        blog3 = Blog.objects.create(
            title="Blog3",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group
        )
        create_notification.s(connection.schema_name, 'created', 'blog.blog', blog3.id, self.user1.id).apply()

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["notifications"]["total"], 2)
        self.assertEqual(data["notifications"]["totalUnread"], 2)
        self.assertEqual(data["notifications"]["edges"][0]["performer"]["guid"], str(self.user1.id))
        self.assertEqual(data["notifications"]["edges"][0]["entity"]["guid"], str(blog3.id))
        self.assertEqual(data["notifications"]["edges"][0]["isUnread"], True)
        self.assertEqual(data["notifications"]["edges"][0]["action"], "created")

        blog3.delete()
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(data["notifications"]["total"], 1)
        self.assertEqual(data["notifications"]["totalUnread"], 1)
        self.assertEqual(data["notifications"]["edges"][0]["action"], "welcome")
