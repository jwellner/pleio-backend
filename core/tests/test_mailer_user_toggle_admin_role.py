from unittest import mock

from django.test import override_settings

from core.lib import get_full_url
from core.mail_builders.user_assign_admin_for_admin import UserAssignAdminForAdminMailer
from core.mail_builders.user_assign_admin_for_user import UserAssignAdminForSelfMailer
from core.mail_builders.user_revoke_admin_for_admin import UserRevokeAdminForAdminMailer
from core.mail_builders.user_revoke_admin_for_user import UserRevokeAdminForSelfMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestMailerUserToggleAdminRoleTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.sender = UserFactory()
        self.admin = AdminFactory()

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_admin_notify_assigned(self, build_context):
        build_context.return_value = {}

        mailer = UserAssignAdminForAdminMailer(user=self.user.guid,
                                               admin=self.admin.guid,
                                               sender=self.sender.guid)

        self.assertDictEqual(mailer.get_context(), {"name_of_user_admin_role_changed": self.user.name,
                                                    "link": get_full_url(self.user.url)})
        self.assertEqual(build_context.call_args.kwargs, {"user": self.sender})
        self.assertEqual(mailer.get_language(), self.admin.get_language())
        self.assertEqual(mailer.get_template(), 'email/user_role_admin_assigned_for_admins.html')
        self.assertEqual(mailer.get_receiver(), self.admin)
        self.assertEqual(mailer.get_receiver_email(), self.admin.email)
        self.assertEqual(mailer.get_sender(), self.sender)
        self.assertEqual(mailer.get_subject(), "A new site administrator was assigned for Pleio 2.0")

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_admin_notify_revoked(self, build_context):
        build_context.return_value = {}

        mailer = UserRevokeAdminForAdminMailer(user=self.user.guid,
                                               admin=self.admin.guid,
                                               sender=self.sender.guid)

        self.assertDictEqual(mailer.get_context(), {"name_of_user_admin_role_changed": self.user.name,
                                                    "link": get_full_url(self.user.url)})
        self.assertEqual(build_context.call_args.kwargs, {"user": self.sender})
        self.assertEqual(mailer.get_language(), self.admin.get_language())
        self.assertEqual(mailer.get_template(), 'email/user_role_admin_removed_for_admins.html')
        self.assertEqual(mailer.get_receiver(), self.admin)
        self.assertEqual(mailer.get_receiver_email(), self.admin.email)
        self.assertEqual(mailer.get_sender(), self.sender)
        self.assertEqual(mailer.get_subject(), "A site administrator was removed from Pleio 2.0")

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_user_notify_assigned(self, build_context):
        build_context.return_value = {}

        mailer = UserAssignAdminForSelfMailer(user=self.user.guid,
                                              sender=self.sender.guid)

        self.assertDictEqual(mailer.get_context(), {"name_of_user_admin_role_changed": self.user.name,
                                                    "link": get_full_url(self.user.url)})
        self.assertEqual(build_context.call_args.kwargs, {"user": self.sender})
        self.assertEqual(mailer.get_language(), self.user.get_language())
        self.assertEqual(mailer.get_template(), 'email/user_role_admin_assigned_for_user.html')
        self.assertEqual(mailer.get_receiver(), self.user)
        self.assertEqual(mailer.get_receiver_email(), self.user.email)
        self.assertEqual(mailer.get_sender(), self.sender)
        self.assertEqual(mailer.get_subject(), "You're granted site administrator right on Pleio 2.0")

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_user_notify_revoked(self, build_context):
        build_context.return_value = {}

        mailer = UserRevokeAdminForSelfMailer(user=self.user.guid,
                                              sender=self.sender.guid)

        self.assertDictEqual(mailer.get_context(), {"name_of_user_admin_role_changed": self.user.name,
                                                    "link": get_full_url(self.user.url)})
        self.assertEqual(build_context.call_args.kwargs, {"user": self.sender})
        self.assertEqual(mailer.get_language(), self.user.get_language())
        self.assertEqual(mailer.get_template(), 'email/user_role_admin_removed_for_user.html')
        self.assertEqual(mailer.get_receiver(), self.user)
        self.assertEqual(mailer.get_receiver_email(), self.user.email)
        self.assertEqual(mailer.get_sender(), self.sender)
        self.assertEqual(mailer.get_subject(), "Your site administrator rights for Pleio 2.0 were removed")
