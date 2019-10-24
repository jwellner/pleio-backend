from django.db import connection
from django.test import TestCase
from django.core.files import File
from django.conf import settings
from backend2.schema import schema
from ariadne import graphql_sync
from ariadne.file_uploads import combine_multipart_data, upload_scalar
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from event.models import Event
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest.mock import MagicMock, patch
from ..models import FileFolder

class EditFileFolderTestCase(TestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.data = {
            "input": {
                "guid": None,
                "title": "",
                "file": "",
            }
        }
        self.mutation = """
            fragment FileFolderParts on FileFolder {
                title
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                mimeType
            }
            mutation ($input: editFileFolderInput!) {
                editFileFolder(input: $input) {
                    entity {
                    guid
                    status
                    ...FileFolderParts
                    }
                }
            }
        """

    @patch("{}.save".format(settings.DEFAULT_FILE_STORAGE))
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_edit_file_title(self, mock_open, mock_save):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_save.return_value = "test.gif"
        mock_open.return_value = file_mock

        test_file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock
        )

        variables = self.data

        variables["input"]["guid"] = test_file.guid
        variables["input"]["title"] = "test123.gif"

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editFileFolder"]["entity"]["title"], variables["input"]["title"])

        test_file.refresh_from_db()

        self.assertEqual(data["editFileFolder"]["entity"]["title"], test_file.title)
        self.assertEqual(data["editFileFolder"]["entity"]["mimeType"], test_file.mime_type)
