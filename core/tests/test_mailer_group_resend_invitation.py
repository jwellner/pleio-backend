from unittest import mock

from mixer.backend.django import mixer

from core.factories import GroupFactory
from core.mail_builders.group_resend_invitation import ResendGroupInvitationMailer
from core.models import GroupInvitation
from core.tests.helpers import PleioTenantTestCase, override_config
from user.factories import UserFactory


class TestMailerGroupResendInvitationTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.ANOTHER_EMAIL = "anonymous@example.com"
        self.user = UserFactory()
        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner)
        self.invitation = mixer.blend(
            GroupInvitation,
            group=self.group,
            invited_user=self.user
        )
        self.anonymous_invitation = mixer.blend(
            GroupInvitation,
            group=self.group,
            email=self.ANOTHER_EMAIL
        )

        self.build_context = mock.patch("core.mail_builders.base.MailerBase.build_context").start()
        self.build_context.return_value = {}
        self.get_language = mock.patch("user.models.User.get_language").start()
        self.get_language.return_value = 'nl'

    @override_config(LANGUAGE='en')
    def test_properties(self):
        mailer = ResendGroupInvitationMailer(sender=self.owner.guid,
                                             invitation=self.invitation.id)
        context = mailer.get_context()
        self.assertEqual(['group_name', 'link'], sorted(context.keys()))
        self.assertEqual(context['group_name'], self.group.name)
        self.assertIn(self.invitation.code, context['link'])

        self.assertEqual(mailer.get_language(), 'nl')
        self.assertEqual(mailer.get_template(), 'email/resend_group_invitation.html')
        self.assertEqual(mailer.get_receiver(), self.user)
        self.assertEqual(mailer.get_receiver_email(), self.user.email)
        self.assertEqual(mailer.get_sender(), self.owner)
        self.assertIn(self.group.name, mailer.get_subject())

    @override_config(LANGUAGE='en')
    def test_properties_anonymous(self):
        mailer = ResendGroupInvitationMailer(sender=self.owner.guid,
                                             invitation=self.anonymous_invitation.id)

        self.assertEqual(mailer.get_receiver(), None)
        self.assertEqual(mailer.get_receiver_email(), self.anonymous_invitation.email)
        self.assertEqual(mailer.get_language(), 'en')
