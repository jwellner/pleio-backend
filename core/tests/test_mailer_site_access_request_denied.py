from unittest import mock

from faker import Faker

from core import config, override_local_config
from core.mail_builders.site_access_request_denied import SiteAccessRequestDeniedMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory


class TestMailerSiteAccessRequestDeniedTestCase(PleioTenantTestCase):
    INTRO = "Some leaving message."

    def setUp(self):
        super().setUp()

        self.EMAIL = Faker().email()
        self.NAME = Faker().name()
        self.sender = AdminFactory()

        self.mailer = SiteAccessRequestDeniedMailer(email=self.EMAIL,
                                                    name=self.NAME,
                                                    sender=self.sender.guid)
        self.switch_language('en')

    @override_local_config(SITE_MEMBERSHIP_DENIED_INTRO=INTRO)
    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            'request_name': self.NAME,
            'intro': self.INTRO,
        })
        self.assertEqual(build_context.call_args.kwargs['user'], self.sender)
        self.assertEqual(self.mailer.get_language(), config.LANGUAGE)
        self.assertEqual(self.mailer.get_template(), 'email/site_access_request_denied.html')
        self.assertEqual(self.mailer.get_receiver(), None)
        self.assertEqual(self.mailer.get_receiver_email(), self.EMAIL)
        self.assertEqual(self.mailer.get_sender(), self.sender)
        self.assertEqual(self.mailer.get_subject(), f'Membership request declined for: {config.NAME}')
