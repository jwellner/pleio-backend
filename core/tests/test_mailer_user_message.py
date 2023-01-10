from unittest import mock

from core.mail_builders.user_send_message import UserSendMessageMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerUserOnDeleteTestCase(PleioTenantTestCase):
    MESSAGE = "Demo message content."
    SUBJECT = "Demo subject"
    SENDER_NAME = "Wilfred of Marcel"

    def setUp(self):
        super().setUp()

        self.sender = UserFactory(name=self.SENDER_NAME)
        self.receiver = UserFactory()
        self.mailer = UserSendMessageMailer(message=self.MESSAGE,
                                            subject=self.SUBJECT,
                                            receiver=self.receiver.guid,
                                            sender=self.sender.guid,
                                            copy=False)
        self.switch_language('en')

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            "message": self.MESSAGE,
            "subject": "Message from Wilfred of Marcel: Demo subject"
        })
        self.assertEqual(self.mailer.get_language(), self.receiver.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/send_message_to_user.html')
        self.assertEqual(self.mailer.get_receiver(), self.receiver)
        self.assertEqual(self.mailer.get_receiver_email(), self.receiver.email)
        self.assertEqual(self.mailer.get_sender(), self.sender)
        self.assertEqual(self.mailer.get_subject(), "Message from Wilfred of Marcel: Demo subject")

    def test_copy(self):
        # When
        self.mailer.copy = True

        # Then
        self.assertEqual(self.mailer.get_subject(), "Copy: Message from Wilfred of Marcel: Demo subject")

