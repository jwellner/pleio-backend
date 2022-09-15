from unittest import mock

from django.test import override_settings

from core.factories import GroupFactory
from core.mail_builders.group_reject_membership import RejectGroupMembershipMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerGroupRejectMembershipTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner)
        self.mailer = RejectGroupMembershipMailer(user=self.user.guid,
                                                  receiver=self.owner.guid,
                                                  group=self.group.guid)

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            "group_name": self.group.name,
        })
        self.assertEqual(self.mailer.get_language(), self.owner.get_language())
        self.assertEqual(self.mailer.get_template(), "email/reject_membership_request.html")
        self.assertEqual(self.mailer.get_receiver(), self.owner)
        self.assertEqual(self.mailer.get_receiver_email(), self.owner.email)
        self.assertEqual(self.mailer.get_sender(), self.user)
        self.assertIn(self.group.name, self.mailer.get_subject())
