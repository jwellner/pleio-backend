from unittest import mock

from django.test import override_settings
from mixer.backend.django import mixer

from core.factories import GroupFactory
from core.mail_builders.group_resend_invitation import ResendGroupInvitationMailer
from core.models import GroupInvitation
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerGroupResendInvitationTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner)
        self.invitation = mixer.blend(GroupInvitation,
                                      group=self.group,
                                      invited_user=self.user)

        self.mailer = ResendGroupInvitationMailer(sender=self.owner.guid,
                                                  invitation=self.invitation.id)

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}

        context = self.mailer.get_context()
        self.assertEqual(['group_name', 'link'], sorted(context.keys()))
        self.assertEqual(context['group_name'], self.group.name)
        self.assertIn(self.invitation.code, context['link'])

        self.assertEqual(self.mailer.get_language(), self.user.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/resend_group_invitation.html')
        self.assertEqual(self.mailer.get_receiver(), self.user)
        self.assertEqual(self.mailer.get_receiver_email(), self.user.email)
        self.assertEqual(self.mailer.get_sender(), self.owner)
        self.assertIn(self.group.name, self.mailer.get_subject())
