from unittest import mock

from core.mail_builders.user_import_success_mailer import UserImportSuccessMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestMailerImportUsersFailedTestCase(PleioTenantTestCase):
    STATS = {
        "created": 10,
        "updated": 20,
        "error": 30,
    }

    def setUp(self):
        super().setUp()
        self.operating_user = UserFactory()
        self.mailer = UserImportSuccessMailer(user=self.operating_user.guid,
                                              stats=self.STATS)
        self.switch_language('en')

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mailer_properties(self, mocked_build_context):
        mocked_build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {
            "stats_created": self.STATS['created'],
            "stats_updated": self.STATS['updated'],
            "stats_error": self.STATS['error'],
        })
        self.assertEqual(self.mailer.get_language(), self.operating_user.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/user_import_success.html')
        self.assertEqual(self.mailer.get_receiver(), self.operating_user)
        self.assertEqual(self.mailer.get_receiver_email(), self.operating_user.email)
        self.assertEqual(self.mailer.get_sender(), None)
        self.assertEqual(self.mailer.get_subject(), "Import was a success")
