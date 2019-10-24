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

class AddEventTestCase(TestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.data = {
            "input": {
                "containerGuid": self.group.guid,
                "file": "test.gif"
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
            mutation ($input: addFileInput!) {
                addFile(input: $input) {
                    entity {
                    guid
                    status
                    ...FileFolderParts
                    }
                }
            }
        """

    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_file(self, mock_open):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["addFile"]["entity"]["title"], file_mock.name)
        self.assertEqual(data["addFile"]["entity"]["mimeType"], file_mock.content_type)
        self.assertEqual(data["addFile"]["entity"]["group"]["guid"], self.group.guid)
