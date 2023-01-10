from unittest import mock

from core.factories import GroupFactory
from core.lib import get_full_url
from core.mail_builders.group_message import SendGroupMessageMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerGroupMessageTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.MESSAGE = "Demo message."
        self.SUBJECT = "Demo subject"
        self.sender = UserFactory()
        self.receiver = UserFactory()
        self.group = GroupFactory(owner=self.sender)
        self.mailer = SendGroupMessageMailer(message=self.MESSAGE,
                                             subject=self.SUBJECT,
                                             receiver=self.receiver.guid,
                                             sender=self.sender.guid,
                                             group=self.group.guid,
                                             copy=False)
        self.switch_language('en')

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertEqual(self.mailer.get_context(), {
            'message': self.MESSAGE,
            'group': self.group.name,
            'group_url': get_full_url(self.group.url)
        })
        self.assertEqual(self.mailer.get_language(), self.receiver.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/send_message_to_group.html')
        self.assertEqual(self.mailer.get_receiver(), self.receiver)
        self.assertEqual(self.mailer.get_receiver_email(), self.receiver.email)
        self.assertEqual(self.mailer.get_sender(), self.sender)
        self.assertIn(self.SUBJECT, self.mailer.get_subject())
        self.assertIn(self.group.name, self.mailer.get_subject())

        self.mailer.copy = True
        self.assertIn("Copy:", self.mailer.get_subject())
