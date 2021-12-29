from django_tenants.test.cases import FastTenantTestCase
from django.core.files import File
from django.conf import settings
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Attachment
from user.models import User
from mixer.backend.django import mixer
from unittest.mock import MagicMock, patch

class AddAttachmentTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedUser2 = mixer.blend(User)

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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_attachment(self, mock_open, mock_mimetype):
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

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        data = result[1]["data"]

        attachment = Attachment.objects.get(id=data["addAttachment"]["attachment"]["id"])

        self.assertEqual(data["addAttachment"]["attachment"]["id"], str(attachment.id))
        self.assertEqual(data["addAttachment"]["attachment"]["url"], attachment.url)
        self.assertEqual(data["addAttachment"]["attachment"]["mimeType"], attachment.mime_type)
        self.assertEqual(data["addAttachment"]["attachment"]["name"], file_mock.name)
