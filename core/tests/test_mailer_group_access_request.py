from unittest import mock

from django.test import override_settings

from core.factories import GroupFactory
from core.lib import obfuscate_email, get_full_url
from core.mail_builders.group_access_request import GroupAccessRequestMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerGroupInviteTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.user = UserFactory()
        self.group = GroupFactory(owner=self.owner)
        self.mailer = GroupAccessRequestMailer(user=self.user.guid,
                                               receiver=self.owner.guid,
                                               group=self.group.guid)

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            "link": get_full_url(self.group.url),
            "group_name": self.group.name,
            "user_obfuscated_email": obfuscate_email(self.user.email),
        })
        self.assertEqual(build_context.call_args.kwargs['user'], self.user)
        self.assertEqual(self.mailer.get_language(), self.owner.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/group_access_request.html')
        self.assertEqual(self.mailer.get_receiver(), self.owner)
        self.assertEqual(self.mailer.get_receiver_email(), self.owner.email)
        self.assertEqual(self.mailer.get_sender(), None)
        self.assertIn(self.group.name, self.mailer.get_subject())
