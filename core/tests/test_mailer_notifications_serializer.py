from mixer.backend.django import mixer
from notifications.signals import notify

from blog.models import Blog
from core.factories import GroupFactory
from core.mail_builders.notifications import serialize_notification
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestSerializeNotificationTestCase(PleioTenantTestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()

        self.author = UserFactory()
        self.recipient = UserFactory()

        self.blog = mixer.blend(Blog, owner=self.author)
        self.expected_result = {
            'performer_name': self.author.name,
            'entity_title': self.blog.title,
            'entity_description': None,
            'entity_type': 'blog',
            'entity_group': False,
            'entity_group_name': '',
            'entity_group_url': '',
            'entity_url': self.blog.url,
            'type_to_string': 'blog',
        }

    def create_notification(self, action_object, verb='created'):
        notification = notify.send(self.author, recipient=[self.recipient], verb=verb, action_object=action_object)[0][1][0]
        self.expected_result['id'] = notification.id
        self.expected_result['action'] = notification.verb
        self.expected_result['timeCreated'] = notification.timestamp
        self.expected_result['isUnread'] = notification.unread

        return notification

    def test_standard_content(self):
        notification = self.create_notification(self.blog)

        response = serialize_notification(notification)
        self.assertDictEqual(response, self.expected_result)

    def test_grouped_content(self):
        group = GroupFactory(owner=self.author)
        self.blog.group = group
        self.blog.save()

        notification = self.create_notification(self.blog)
        response = serialize_notification(notification)

        self.expected_result['entity_group'] = True
        self.expected_result['entity_group_name'] = group.name
        self.expected_result['entity_group_url'] = group.url
        self.expected_result['entity_url'] = self.blog.url
        self.assertDictEqual(response, self.expected_result)

