import os
from unittest import mock

from django.utils.translation import gettext
from mixer.backend.django import mixer

from core.mail_builders.avatar_export_ready import AvatarExportReadyMailer
from core.models import AvatarExport
from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory


class TestAvatarExportNotificationTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.initiator = AdminFactory()
        self.file = self.file_factory(self.relative_path(__file__, ["assets", "avatar_export.zip"]))
        self.avatar_export: AvatarExport = mixer.blend(AvatarExport,
                                                       initiator=self.initiator,
                                                       file=self.file)

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mailer_properties(self, mocked_build_context):
        mocked_build_context.return_value = {}
        self.mailer = AvatarExportReadyMailer(avatar_export=self.avatar_export.guid)

        self.assertDictEqual(self.mailer.get_context(), {"download_url": self.avatar_export.file.download_url,
                                                         "filename": self.avatar_export.file.title})
        self.assertEqual(mocked_build_context.call_args.kwargs, {"user": self.initiator})

        self.assertEqual(self.mailer.get_language(), self.initiator.get_language())
        self.assertEqual(self.mailer.get_subject(), gettext("Avatar export is ready"))
        self.assertEqual(self.mailer.get_sender(), None)
        self.assertEqual(self.mailer.get_template(), 'email/avatar_export_ready.html')
        self.assertEqual(self.mailer.get_receiver(), self.initiator)
        self.assertEqual(self.mailer.get_receiver_email(), self.initiator.email)

    @mock.patch('core.utils.export.build_avatar_export')
    @mock.patch('core.mail_builders.avatar_export_ready.schedule_avatar_export_ready_mail')
    def test_called_at_the_end_of_building_the_export(self, mocked_send_mail, mocked_build_export):
        from core.tasks.exports import export_avatars
        mocked_build_export.return_value = "nothing to report"

        export_avatars(self.tenant.schema_name, self.avatar_export.guid)

        self.assertTrue(mocked_send_mail.called)
        self.assertEqual(mocked_send_mail.call_args.args[0], self.avatar_export)
