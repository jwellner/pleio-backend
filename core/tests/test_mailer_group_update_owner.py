from unittest import mock

from django.test import override_settings

from core.factories import GroupFactory
from core.lib import get_full_url
from core.mail_builders.group_change_ownership import ChangeGroupOwnershipMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerGroupUpdateOwnerTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.sender = UserFactory()
        self.group = GroupFactory(owner=self.sender)

        self.mailer = ChangeGroupOwnershipMailer(user=self.user.guid,
                                                 sender=self.sender.guid,
                                                 group=self.group.guid)

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            "link": get_full_url(self.group.url),
            "group_name": self.group.name
        })
        self.assertEqual(build_context.call_args.kwargs['user'], self.sender)
        self.assertEqual(self.mailer.get_language(), self.user.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/group_ownership_transferred.html')
        self.assertEqual(self.mailer.get_receiver(), self.user)
        self.assertEqual(self.mailer.get_receiver_email(), self.user.email)
        self.assertEqual(self.mailer.get_sender(), self.sender)
        self.assertIn(self.group.name, self.mailer.get_subject())
