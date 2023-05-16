from unittest import mock

from django.test import override_settings
from faker import Faker
from mixer.backend.django import mixer

from core import config
from core.mail_builders.invite_to_site import InviteToSiteMailer
from core.models import SiteInvitation
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerInviteToSiteTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.invitation: SiteInvitation = mixer.blend(SiteInvitation)
        self.sender = UserFactory()
        self.MESSAGE = Faker().sentence()

        self.mailer = InviteToSiteMailer(sender=self.sender.guid,
                                         email=self.invitation.email,
                                         message=self.MESSAGE)
        self.switch_language('en')

    @override_settings(ENV='test')
    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            'link': f'https://{self.tenant.primary_domain}/login?invitecode={self.invitation.code}',
            'message': self.MESSAGE,
        })
        self.assertEqual(build_context.call_args.kwargs['user'], self.sender)
        self.assertEqual(self.mailer.get_language(), config.LANGUAGE)
        self.assertEqual(self.mailer.get_template(), 'email/invite_to_site.html')
        self.assertEqual(self.mailer.get_receiver(), None)
        self.assertEqual(self.mailer.get_receiver_email(), self.invitation.email)
        self.assertEqual(self.mailer.get_sender(), self.sender)
        self.assertEqual(self.mailer.get_subject(), f'You are invited to join site {config.NAME}')
