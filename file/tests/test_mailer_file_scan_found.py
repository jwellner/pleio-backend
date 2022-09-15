from unittest import mock

from django.test import override_settings

from core.tests.helpers import PleioTenantTestCase
from file.mail_builders.file_scan_found import FileScanFoundMailer
from user.factories import AdminFactory


class TestMailerFileScanFoundTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.virus_count = 42

        self.mailer = FileScanFoundMailer(admin=self.admin.guid,
                                          virus_count=self.virus_count)

    @override_settings(ENV='test')
    @override_settings(LANGUAGE_CODE='en')
    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            'virus_count': self.virus_count,
        })
        self.assertEqual(self.mailer.get_language(), self.admin.get_language())
        self.assertEqual(self.mailer.get_template(), "email/file_scan_found.html")
        self.assertEqual(self.mailer.get_receiver(), self.admin)
        self.assertEqual(self.mailer.get_receiver_email(), self.admin.email)
        self.assertEqual(self.mailer.get_sender(), None)
        self.assertEqual(self.mailer.get_subject(), "Filescan found suspicous files on https://tenant.fast-test.com")

