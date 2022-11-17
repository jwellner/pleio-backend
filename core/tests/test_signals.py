from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group, Comment, Annotation
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from unittest import mock


class SignalsTestCase(FastTenantTestCase):

    def setUp(self):
        super().setUp()
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

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.group.delete()
        self.user1.delete()
        self.user2.delete()
        super().tearDown()

    @mock.patch('core.tasks.create_notification.delay')
    def test_follow_after_comment(self, __):
        commentingUser = mixer.blend(User)

        Comment.objects.create(owner=commentingUser, container=self.blog1)

        annotations = Annotation.objects.filter(user=commentingUser, object_id=self.blog1.id, key='followed')
        self.assertEqual(len(annotations), 1)

    @mock.patch('core.tasks.create_notification.delay')
    def test_follow_once_after_multiple_comment(self, __):
        commentingUser = mixer.blend(User)

        Comment.objects.create(owner=commentingUser, container=self.blog1)
        Comment.objects.create(owner=commentingUser, container=self.blog1)

        annotations = Annotation.objects.filter(user=commentingUser, object_id=self.blog1.id, key='followed')
        self.assertEqual(len(annotations), 1)

    @mock.patch('core.tasks.create_notification.delay')
    def test_notification_handler(self, mocked_create_notification):
        self.blog3 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group
        )

        mocked_create_notification.assert_called_once_with(connection.schema_name, 'created', 'blog.blog', self.blog3.id, self.blog3.owner.id)

    @mock.patch('core.tasks.create_notification.delay')
    def test_mention_handler(self, mocked_create_notification):
        tiptap = {
            'type': 'doc',
            'content': [
                {
                    'type': 'mention',
                    'attrs': {
                        'id': '1234-1234-1234-12',
                        'label': 'user X'
                    },
                }
            ],
        }

        self.blog1.rich_description = tiptap
        self.blog1.save()

        mocked_create_notification.assert_called_once_with(connection.schema_name, 'mentioned', 'blog.blog', self.blog1.id, self.blog1.owner.id)
