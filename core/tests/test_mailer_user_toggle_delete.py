from unittest import mock

from core.mail_builders.user_cancel_delete_for_admin import UserCancelDeleteToAdminMailer
from core.mail_builders.user_cancel_delete_for_user import UserCancelDeleteToSelfMailer
from core.mail_builders.user_request_delete_for_admin import UserRequestDeleteToAdminMailer
from core.mail_builders.user_request_delete_for_user import UserRequestDeleteToSelfMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestMailerUserOnDeleteTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()

        self.switch_language('en')

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_schedule_user_cancel_delete_for_admin_mail(self, build_context):
        build_context.return_value = mock.MagicMock()

        mailer = UserCancelDeleteToAdminMailer(user=self.user.guid,
                                               admin=self.admin.guid)

        self.assertEqual(mailer.get_context(), build_context.return_value)
        self.assertEqual(build_context.call_args.kwargs, {'user': self.user})
        self.assertEqual(mailer.get_language(), self.admin.get_language())
        self.assertEqual(mailer.get_template(), 'email/toggle_request_delete_user_cancelled_admin.html')
        self.assertEqual(mailer.get_receiver(), self.admin)
        self.assertEqual(mailer.get_receiver_email(), self.admin.email)
        self.assertEqual(mailer.get_sender(), self.user)
        self.assertEqual(mailer.get_subject(), "Request to remove account cancelled")

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_schedule_user_cancel_delete_for_user_mail(self, build_context):
        build_context.return_value = mock.MagicMock()

        mailer = UserCancelDeleteToSelfMailer(user=self.user.guid)

        self.assertEqual(mailer.get_context(), build_context.return_value)
        self.assertEqual(build_context.call_args.kwargs, {'user': self.user})
        self.assertEqual(mailer.get_language(), self.user.get_language())
        self.assertEqual(mailer.get_template(), 'email/toggle_request_delete_user_cancelled.html')
        self.assertEqual(mailer.get_receiver(), self.user)
        self.assertEqual(mailer.get_receiver_email(), self.user.email)
        self.assertEqual(mailer.get_sender(), None)
        self.assertEqual(mailer.get_subject(), "Request to remove account cancelled")

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_schedule_user_request_delete_for_admin_mail(self, build_context):
        build_context.return_value = mock.MagicMock()

        mailer = UserRequestDeleteToAdminMailer(user=self.user.guid,
                                               admin=self.admin.guid)

        self.assertEqual(mailer.get_context(), build_context.return_value)
        self.assertEqual(build_context.call_args.kwargs, {'user': self.user})
        self.assertEqual(mailer.get_language(), self.admin.get_language())
        self.assertEqual(mailer.get_template(), 'email/toggle_request_delete_user_requested_admin.html')
        self.assertEqual(mailer.get_receiver(), self.admin)
        self.assertEqual(mailer.get_receiver_email(), self.admin.email)
        self.assertEqual(mailer.get_sender(), self.user)
        self.assertEqual(mailer.get_subject(), "Request to remove account")

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_schedule_user_request_delete_for_user_mail(self, build_context):
        build_context.return_value = mock.MagicMock()

        mailer = UserRequestDeleteToSelfMailer(user=self.user.guid)

        self.assertEqual(mailer.get_context(), build_context.return_value)
        self.assertEqual(build_context.call_args.kwargs, {'user': self.user})
        self.assertEqual(mailer.get_language(), self.user.get_language())
        self.assertEqual(mailer.get_template(), 'email/toggle_request_delete_user_requested.html')
        self.assertEqual(mailer.get_receiver(), self.user)
        self.assertEqual(mailer.get_receiver_email(), self.user.email)
        self.assertEqual(mailer.get_sender(), None)
        self.assertEqual(mailer.get_subject(), "Request to remove account")
