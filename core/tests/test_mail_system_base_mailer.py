from django.test import override_settings

from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailSystemBaseMailerTestCase(PleioTenantTestCase):

    @override_settings(ENV='local')
    def test_template_mailer_build_context_on_user(self):
        from core.mail_builders.base import MailerBase

        user = UserFactory()
        mailer = MailerBase()
        context = mailer.build_context(user=user)

        self.assertEqual(7, len(context))
        self.assertEqual(context['site_url'], 'http://tenant.fast-test.com:8000')
        self.assertEqual(context['site_name'], 'Pleio 2.0')
        self.assertEqual(context['primary_color'], '#0e2f56')
        self.assertEqual(context['header_color'], '#0e2f56')
        self.assertIn("http://tenant.fast-test.com:8000/edit_email_settings/", context['mail_settings_url'])
        self.assertIn(user.url, context['user_url'])
        self.assertIn(context['user_name'], user.name)

    @override_settings(ENV='local')
    def test_template_mailer_build_context_on_mail_info(self):
        from core.mail_builders.base import MailerBase

        user = UserFactory()
        mailer = MailerBase()
        context = mailer.build_context(mail_info=user.as_mailinfo())

        self.assertEqual(5, len(context))
        self.assertEqual(context['site_url'], 'http://tenant.fast-test.com:8000')
        self.assertEqual(context['site_name'], 'Pleio 2.0')
        self.assertEqual(context['primary_color'], '#0e2f56')
        self.assertEqual(context['header_color'], '#0e2f56')
        self.assertIn(context['user_name'], user.name)

    @override_settings(ENV='local')
    def test_template_mailer_build_context_on_nothing(self):
        from core.mail_builders.base import MailerBase

        mailer = MailerBase()
        context = mailer.build_context()

        self.assertEqual(4, len(context))
        self.assertEqual(context['site_url'], 'http://tenant.fast-test.com:8000')
        self.assertEqual(context['site_name'], 'Pleio 2.0')
        self.assertEqual(context['primary_color'], '#0e2f56')
        self.assertEqual(context['header_color'], '#0e2f56')
