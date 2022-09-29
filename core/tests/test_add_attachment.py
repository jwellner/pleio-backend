from django.core.files import File
from django.conf import settings
from core.models import Attachment
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from unittest.mock import MagicMock, patch


class AddAttachmentTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddAttachmentTestCase, self).setUp()

        self.authenticatedUser = UserFactory()
        self.authenticatedUser2 = UserFactory()

        self.mutation = """
            mutation addAttachment($input: addAttachmentInput!) {
                addAttachment(input: $input) {
                    attachment {
                        id
                        url
                        mimeType
                        name
                    }
                }
            }
        """

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_attachment_anonymous(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = {
            "input": {
                "file": "test.gif",
            }
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation, variables)

    @patch("core.models.attachment.strip_exif")
    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_attachment(self, mock_open, mock_mimetype, mocked_strip_exif):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = {
            "input": {
                "file": "test.gif",
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        attachment = Attachment.objects.get(id=data["addAttachment"]["attachment"]["id"])
        self.assertEqual(data["addAttachment"]["attachment"]["id"], str(attachment.id))
        self.assertEqual(data["addAttachment"]["attachment"]["url"], attachment.url)
        self.assertEqual(data["addAttachment"]["attachment"]["mimeType"], attachment.mime_type)
        self.assertEqual(data["addAttachment"]["attachment"]["name"], file_mock.name)
        self.assertTrue(mocked_strip_exif.called)
