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
from ..models import FileFolder

class MoveFileFolderTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.folder = FileFolder.objects.create(
            title="images",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_folder=True
        )

        self.file = FileFolder.objects.create(
            title="file.jpg",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
        )


        self.data = {
            "input": {
                "guid": None,
                "containerGuid": None,
            }
        }
        self.mutation = """
            fragment FileFolderParts on FileFolder {
                title
                parentFolder {
                    guid
                }
                group {
                    guid
                }
            }
            mutation ($input: moveFileFolderInput!) {
                moveFileFolder(input: $input) {
                    entity {
                        guid
                        status
                        ...FileFolderParts
                    }
                }
            }
        """

    def test_move_file_to_folder(self):

        variables = self.data

        variables["input"]["guid"] = self.file.guid
        variables["input"]["containerGuid"] = self.folder.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["moveFileFolder"]["entity"]["parentFolder"]["guid"], self.folder.guid)

    def test_move_file_to_group(self):

        variables = self.data

        variables["input"]["guid"] = self.file.guid
        variables["input"]["containerGuid"] = self.group.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["moveFileFolder"]["entity"]["parentFolder"], None)
        self.assertEqual(data["moveFileFolder"]["entity"]["group"]["guid"], self.group.guid)

    def test_move_folder_to_group(self):

        variables = self.data

        variables["input"]["guid"] = self.folder.guid
        variables["input"]["containerGuid"] = self.group.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["moveFileFolder"]["entity"]["parentFolder"], None)
        self.assertEqual(data["moveFileFolder"]["entity"]["group"]["guid"], self.group.guid)
