from unittest.mock import patch

from django.db import connection
from django.core.cache import cache
from mixer.backend.django import mixer
from notifications.admin import Notification
from notifications.models import Notification
from notifications.signals import notify
from unittest import mock

from core.factories import GroupFactory
from core.models import Comment
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from blog.models import Blog
from core.constances import ACCESS_TYPE
from core.models.push_notification import WebPushSubscription
from core.tasks import create_notification


class NotificationsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        # let the test explicitly add notifications.
        self.mocked_create_notification = patch('core.tasks.create_notification.delay').start()

        self.user1 = UserFactory(email="group-owner@example.com")
        self.user2 = UserFactory(email="member@example.com")
        self.group = GroupFactory(owner=self.user1,
                                  auto_notification=True)
        self.group.join(self.user2, 'member')


        self.blog1 = Blog.objects.create(
            title="From the group owner",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.blog2 = Blog.objects.create(
            title="Another from the group owner",
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

        self.assertTrue(Notification.objects.all())

        data = result["data"]
        self.assertEqual(data["notifications"]["edges"][0]["performer"]["guid"], str(self.user1.id))
        self.assertEqual(data["notifications"]["edges"][0]["container"], None)
        self.assertEqual(data["notifications"]["edges"][0]["entity"]["guid"], str(self.user1.id))

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


class DirectNotificationsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        cache.set("%s%s" % (connection.schema_name, 'PUSH_NOTIFICATIONS_ENABLED'), True)

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.group = GroupFactory(owner=self.user1,
                                  auto_notification=True)

        self.group.join(self.user2, 'member')

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.follow1 = self.blog1.add_follow(self.user2)
        self.follow2 = self.blog2.add_follow(self.user2)
        self.comment1 = Comment.objects.create(
            owner=self.user1,
            container=self.blog1,
            rich_description='{"type":"doc","content":[{"type":"paragraph","attrs":{"intro":false},"content":[{"type":"mention","attrs":{"id":"' + str(self.user2.id) + '","label":"JanHotmail#14"}},{"type":"text","text":"  test"}]}]}'
        )
        self.comment2 = Comment.objects.create(
            owner=self.user1,
            container=self.blog2,
            rich_description='{"type":"doc","content":[{"type":"paragraph","attrs":{"intro":false},"content":[{"type":"mention","attrs":{"id":"' + str(self.user2.id) + '","label":"JanHotmail#14"}},{"type":"text","text":"  test"}]}]}'
        )

        self.subscription = mixer.blend(WebPushSubscription, user=self.user2)


    def create_notification(self, action_object, verb='created'):
        notification = notify.send(self.user1, recipient=[self.user2], verb=verb, action_object=action_object)[0][1][0]
        return notification

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.group.delete()
        self.user2.delete()
        self.user1.delete()
        super().tearDown()


    #test direct mail outside groups
    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notification_direct_mail_comment_send(self, schedule_notification_mail):
        self.user2.profile.is_comment_notification_direct_mail_enabled = True
        self.user2.profile.save()
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog2.id, self.user1.id).apply()
        schedule_notification_mail.assert_called_once()

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notification_direct_mail_comment_not_send(self, schedule_notification_mail):
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog2.id, self.user1.id).apply()
        schedule_notification_mail.assert_not_called()

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    @mock.patch('user.models.UserManager.get_unmentioned_users')
    def test_notification_direct_mail_mention_send(self, mocked_get_unmentioned_users, mocked_schedule_notification_mail):
        mocked_get_unmentioned_users.return_value = [self.user2]
        self.user2.profile.is_mention_notification_direct_mail_enabled = True
        self.user2.profile.save()
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment2.id, self.user1.id).apply()
        mocked_schedule_notification_mail.assert_called_once()

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notification_direct_mail_mention_not_send(self, schedule_notification_mail):
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment2.id, self.user1.id).apply()
        schedule_notification_mail.assert_not_called()



    # test with general comment notifications disabled
    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notification_direct_mail_comment_notifications_disabled_not_send(self, schedule_notification_mail):
        self.user2.profile.is_comment_notifications_enabled = False
        self.user2.profile.is_comment_notification_direct_mail_enabled = True
        self.user2.profile.save()
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog2.id, self.user1.id).apply()
        schedule_notification_mail.assert_not_called()
    
    # test with general mention notifications disabled
    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notification_direct_mail_mention_notifications_disabled_not_send(self, schedule_notification_mail):
        self.user2.profile.is_mention_notifications_enabled = False
        self.user2.profile.is_mention_notification_direct_mail_enabled = True
        self.user2.profile.save()
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment2.id, self.user1.id).apply()
        schedule_notification_mail.assert_not_called()

    #test direct mail in groups
    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notification_direct_mail_comment_in_group_send(self, schedule_notification_mail):
        self.group.set_member_is_notification_direct_mail_enabled(self.user2, True)
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog1.id, self.user1.id).apply()
        schedule_notification_mail.assert_called_once()

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notification_direct_mail_comment_in_group_not_send(self, schedule_notification_mail):
        self.group.set_member_is_notification_direct_mail_enabled(self.user2, False)
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog1.id, self.user1.id).apply()
        schedule_notification_mail.assert_not_called()

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    @mock.patch('user.models.UserManager.get_unmentioned_users')
    def test_notification_direct_mail_mention_in_group_send(self, mocked_get_unmentioned_users, schedule_notification_mail):
        mocked_get_unmentioned_users.return_value = [self.user2]
        self.group.set_member_is_notification_direct_mail_enabled(self.user2, True)
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment1.id, self.user1.id).apply()
        schedule_notification_mail.assert_called_once()

    @mock.patch('core.mail_builders.notifications.schedule_notification_mail')
    def test_notification_direct_mail_mention_in_group_not_send(self, schedule_notification_mail):
        self.group.set_member_is_notification_direct_mail_enabled(self.user2, False)
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment1.id, self.user1.id).apply()
        schedule_notification_mail.assert_not_called()


    #test push outside groups
    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    def test_notification_push_comment_send(self, send_web_push_notification):
        self.user2.profile.is_comment_notification_push_enabled = True
        self.user2.profile.save()
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog2.id, self.user1.id).apply()
        send_web_push_notification.assert_called_once()

    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    def test_notification_push_comment_not_send(self, send_web_push_notification):
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog2.id, self.user1.id).apply()
        send_web_push_notification.assert_not_called()

    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    @mock.patch('user.models.UserManager.get_unmentioned_users')
    def test_notification_push_mention_send(self, mocked_get_unmentioned_users, send_web_push_notification):
        mocked_get_unmentioned_users.return_value = [self.user2]
        self.user2.profile.is_mention_notification_push_enabled = True
        self.user2.profile.save()
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment2.id, self.user1.id).apply()
        send_web_push_notification.assert_called_once()

    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    def test_notification_push_mention_not_send(self, send_web_push_notification):
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment2.id, self.user1.id).apply()
        send_web_push_notification.assert_not_called()

    # test with general comment notifications disabled
    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    def test_notification_push_comment_notifications_disabled_not_send(self, send_web_push_notification):
        self.user2.profile.is_comment_notifications_enabled = False
        self.user2.profile.is_comment_notification_push_enabled = True
        self.user2.profile.save()
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog2.id, self.user1.id).apply()
        send_web_push_notification.assert_not_called()
    
    # test with general mention notifications disabled
    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    def test_notification_push_mention_notifications_disabled_not_send(self, send_web_push_notification):
        self.user2.profile.is_mention_notifications_enabled = False
        self.user2.profile.is_mention_notification_push_enabled = True
        self.user2.profile.save()
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment2.id, self.user1.id).apply()
        send_web_push_notification.assert_not_called()

    #test push notifications in groups
    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    def test_notification_push_comment_in_group_send(self, send_web_push_notification):
        self.group.set_member_is_notification_push_enabled(self.user2, True)
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog1.id, self.user1.id).apply()
        send_web_push_notification.assert_called_once()

    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    def test_notification_push_comment_in_group_not_send(self, send_web_push_notification):
        self.group.set_member_is_notification_push_enabled(self.user2, False)
        create_notification.s(connection.schema_name, 'commented', 'blog.blog', self.blog1.id, self.user1.id).apply()
        send_web_push_notification.assert_not_called()

    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    @mock.patch('user.models.UserManager.get_unmentioned_users')
    def test_notification_push_mention_in_group_send(self, mocked_get_unmentioned_users, send_web_push_notification):
        mocked_get_unmentioned_users.return_value = [self.user2]
        self.group.set_member_is_notification_push_enabled(self.user2, True)
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment1.id, self.user1.id).apply()
        send_web_push_notification.assert_called_once()

    @mock.patch('core.tasks.notification_tasks.send_web_push_notification')
    def test_notification_push_mention_in_group_not_send(self, send_web_push_notification):
        self.group.set_member_is_notification_push_enabled(self.user2, False)
        create_notification.s(connection.schema_name, 'mentioned', 'core.comment', self.comment1.id, self.user1.id).apply()
        send_web_push_notification.assert_not_called()
