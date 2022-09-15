from unittest import mock

from django.test import override_settings

from core import config
from core.mail_builders.site_access_changed import SiteAccessChangedMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestMailerSiteAccessChangedTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.sender = UserFactory()
        self.is_closed = True

        self.mailer = SiteAccessChangedMailer(admin=self.admin.guid,
                                              sender=self.sender.guid,
                                              is_closed=self.is_closed)

    @override_settings(LANGUAGE_CODE='en')
    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            'access_level': 'closed',
        })
        self.assertEqual(build_context.call_args.kwargs['user'], self.sender)
        self.assertEqual(self.mailer.get_language(), self.admin.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/site_access_changed.html')
        self.assertEqual(self.mailer.get_receiver(), self.admin)
        self.assertEqual(self.mailer.get_receiver_email(), self.admin.email)
        self.assertEqual(self.mailer.get_sender(), self.sender)
        self.assertEqual(self.mailer.get_subject(), f'Site access level changed for {config.NAME}')
