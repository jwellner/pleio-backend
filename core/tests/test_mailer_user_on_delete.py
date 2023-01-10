from unittest import mock

from core.mail_builders.user_delete_complete import UserDeleteCompleteMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerUserOnDeleteTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.switch_language('en')

        user = UserFactory()
        self.user_info = user.as_mailinfo()
        user.delete()

        self.receiver = UserFactory()
        self.sender = UserFactory()

        self.mailer = UserDeleteCompleteMailer(
            user_info=self.user_info,
            receiver_info=self.receiver.as_mailinfo(),
            sender=self.sender.guid,
            to_admin=False
        )

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {'name_deleted_user': self.user_info['name']})
        self.assertEqual(self.mailer.get_language(), self.receiver.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/admin_user_deleted.html')
        self.assertEqual(self.mailer.get_receiver(), self.receiver)
        self.assertEqual(self.mailer.get_receiver_email(), self.receiver.email)
        self.assertEqual(self.mailer.get_sender(), self.sender)
        self.assertIn(self.user_info['name'], self.mailer.get_subject())

    def test_properties_when_receiver_is_deleted(self):
        # When
        self.receiver.delete()

        # Then
        self.assertEqual(self.mailer.get_receiver(), None)

    def test_properties_when_send_to_admin(self):
        # When
        self.mailer.to_admin = True

        # Then
        self.assertEqual(self.mailer.get_subject(), "A site administrator was removed from Pleio 2.0")
