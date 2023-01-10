from unittest import mock

import faker

from core.factories import GroupFactory
from core.lib import get_full_url
from core.mail_builders.group_invite_to_group import InviteToGroupMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerGroupInviteTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner)
        self.switch_language('en')

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}
        EMAIL = faker.Faker().email()
        LANGCODE = faker.Faker().word()

        mailer = InviteToGroupMailer(email=EMAIL,
                                     sender=self.owner.guid,
                                     language=LANGCODE,
                                     group=self.group.guid)

        self.assertDictEqual(mailer.get_context(), {
            "link": get_full_url(self.group.url),
            "group_name": self.group.name
        })
        self.assertEqual(build_context.call_args.kwargs['user'], self.owner)
        self.assertEqual(mailer.get_language(), LANGCODE)
        self.assertEqual(mailer.get_template(), 'email/invite_to_group.html')
        self.assertEqual(mailer.get_receiver(), None)
        self.assertEqual(mailer.get_receiver_email(), EMAIL)
        self.assertEqual(mailer.get_sender(), self.owner)
        self.assertIn(self.group.name, mailer.get_subject())

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_user_properties(self, build_context):
        build_context.return_value = {}
        user = UserFactory()
        mailer = InviteToGroupMailer(user=user.guid,
                                     sender=self.owner.guid,
                                     group=self.group.guid)

        self.assertDictEqual(mailer.get_context(), {
            "link": get_full_url(self.group.url),
            "group_name": self.group.name
        })
        self.assertEqual(build_context.call_args.kwargs['user'], self.owner)
        self.assertEqual(mailer.get_language(), user.get_language())
        self.assertEqual(mailer.get_template(), 'email/invite_to_group.html')
        self.assertEqual(mailer.get_receiver(), user)
        self.assertEqual(mailer.get_receiver_email(), user.email)
        self.assertEqual(mailer.get_sender(), self.owner)
        self.assertIn(self.group.name, mailer.get_subject())
