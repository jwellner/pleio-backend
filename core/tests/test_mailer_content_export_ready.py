from unittest import mock

from django.core.files.base import ContentFile

from core.lib import get_full_url
from core.mail_builders.content_export_ready import ContentExportReadyMailer
from core.tests.helpers import PleioTenantTestCase
from file.factories import FileFactory
from user.factories import UserFactory


class TestMailerContentExportReadyTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.file_folder = FileFactory(owner=self.owner,
                                       upload=ContentFile(b"Maybe zipfile", 'activities.zip'))

        self.mailer = ContentExportReadyMailer(file_folder=self.file_folder.guid,
                                               owner=self.owner.guid)

        self.switch_language('en')

    def tearDown(self):
        self.file_folder.delete()
        self.owner.delete()

        super().tearDown()

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_properties(self, build_context):
        build_context.return_value = {}

        self.assertEqual(self.mailer.get_context(), {
            "download_url": get_full_url(self.file_folder.download_url)
        })
        self.assertEqual(build_context.call_args.kwargs, {
            "user": self.owner
        })

        self.assertEqual(self.mailer.get_language(), self.owner.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/content_export_ready.html')
        self.assertEqual(self.mailer.get_receiver(), self.owner)
        self.assertEqual(self.mailer.get_receiver_email(), self.owner.email)
        self.assertEqual(self.mailer.get_sender(), None)
        self.assertEqual(self.mailer.get_subject(), 'Your content export is ready')
