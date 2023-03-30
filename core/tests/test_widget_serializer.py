from unittest import mock

from django.conf import settings
from django.core.files import File

from core.exceptions import AttachmentVirusScanError
from core.models import Attachment
from core.tests.helpers import PleioTenantTestCase
from core.utils.clamav import FileScanError, FILE_SCAN
from core.widget_resolver import WidgetSerializer
from user.factories import UserFactory


class TestWidgetSerializerTestCase(PleioTenantTestCase):
    """ Test specifics on the core.widget_resolver.WidgetSerializer """

    def setUp(self):
        super().setUp()

        self.acting_user = UserFactory()

        self.file_mock = mock.MagicMock(spec=File)
        self.file_mock.name = 'test.gif'
        self.file_mock.content_type = 'image/gif'

        self.mocked_mimetype = mock.patch("core.lib.get_mimetype").start()
        self.mocked_mimetype.return_value = self.file_mock.content_type

        self.mocked_open = mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE)).start()
        self.mocked_open.return_value = self.file_mock

        self.widget_spec = {
            'type': "demo",
            'settings': [{"key": "attachment",
                          "attachment": self.file_mock.name}]
        }

        self.scan = mock.patch("core.utils.clamav.scan").start()

    def test_contains_attachment(self):
        widget = WidgetSerializer(self.widget_spec, self.acting_user).serialize()
        attachment = Attachment.objects.first()

        self.assertEqual(attachment.name, self.file_mock.name)
        self.assertEqual({**widget}, {
            'type': 'demo',
            'settings': [
                {'key': 'attachment',
                 'value': None,
                 'richDescription': None,
                 'attachmentId': attachment.guid}
            ]
        })

    def test_contains_attachment_with_virus(self):
        # Given.
        self.scan.side_effect = FileScanError(FILE_SCAN.VIRUS, "NL.SARS-PLEIO.Z665+")

        try:
            # When.
            WidgetSerializer(self.widget_spec, self.acting_user).serialize()
            self.fail("Unexpectedly did not respond correctly to the virus found behaviour")  # pragma: no cover
        except AttachmentVirusScanError as e:
            # Then.
            self.assertEqual(str(e), self.file_mock.name)
