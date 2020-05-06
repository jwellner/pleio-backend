from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.core.files import File
from django.conf import settings
from backend2.schema import schema
from ariadne import graphql_sync
from ariadne.file_uploads import combine_multipart_data, upload_scalar
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from event.models import Event
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest.mock import MagicMock, patch

class AddImageTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.data = {
            "input": {
                "image": "test.gif"
            }
        }
        self.mutation = """
            mutation addImage($input: addImageInput!) {
                addImage(input: $input) {
                    file {      
                        guid
                        url
                    }
                }
            }
        """

    @patch("file.models.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_image(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value=request)

        data = result[1]["data"]

        self.assertIsNotNone(data["addImage"]["file"]["guid"])
        self.assertIsNotNone(data["addImage"]["file"]["url"])
