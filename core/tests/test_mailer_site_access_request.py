from unittest import mock

from django.test import override_settings
from faker import Faker

from core import config
from core.mail_builders.site_access_request import SiteAccessRequestMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory


class TestMailerSiteAccessRequestTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.NAME = Faker().name()
        self.admin = AdminFactory()

        self.mailer = SiteAccessRequestMailer(admin=self.admin.guid,
                                              name=self.NAME)
        self.switch_language('en')

    @override_settings(ENV='test')
    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            'request_name': self.NAME,
            'site_admin_url': "https://%s/admin/users/access-requests" % self.tenant.primary_domain,
            'admin_name': self.admin.name,
        })
        self.assertEqual(self.mailer.get_language(), self.admin.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/site_access_request.html')
        self.assertEqual(self.mailer.get_receiver(), self.admin)
        self.assertEqual(self.mailer.get_receiver_email(), self.admin.email)
        self.assertEqual(self.mailer.get_sender(), None)
        self.assertEqual(self.mailer.get_subject(), f'New access request for {config.NAME}')
