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
from core.models import Group, User
from event.models import Event
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest.mock import MagicMock, patch
from ..models import FileFolder

class EditFileFolderTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.user1 = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.authenticatedUser)
        self.group.join(self.user1, 'member')
        self.folder1 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.folder2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=self.folder1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.folder3 = FileFolder.objects.create(
            owner=self.user1,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.file = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            is_folder=False,
            group=self.group,
            parent=self.folder2,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            is_folder=False,
            group=self.group,
            parent=self.folder3,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.group = mixer.blend(Group, owner=self.authenticatedUser)
        self.folder1 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.folder2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=self.folder1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            is_folder=False,
            group=self.group,
            parent=self.folder2,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

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
        variables["input"]["tags"] = ["tag_one", "tag_two"]

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editFileFolder"]["entity"]["title"], variables["input"]["title"])

        test_file.refresh_from_db()

        self.assertEqual(data["editFileFolder"]["entity"]["title"], test_file.title)
        self.assertEqual(data["editFileFolder"]["entity"]["mimeType"], test_file.mime_type)
        self.assertEqual(data["editFileFolder"]["entity"]["tags"][0], "tag_one")
        self.assertEqual(data["editFileFolder"]["entity"]["tags"][1], "tag_two")

    def test_edit_folder_access_ids_recursive(self):

        mutation = """
            mutation editFileFolder($input: editFileFolderInput!) {
            editFileFolder(input: $input) {
                entity {
                guid
                ... on FileFolder {
                    accessId
                    writeAccessId
                    __typename
                }
                __typename
                }
                __typename
            }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "input": {
                "guid": self.folder1.guid,
                "accessId": 1,
                "writeAccessId": 1,
                "isAccessRecursive": True
            }
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["editFileFolder"]["entity"]["guid"], self.folder1.guid)
        self.assertEqual(data["editFileFolder"]["entity"]["__typename"], "FileFolder")

        query = """
            query OpenFolder($guid: String, $filter: String) {
                files(containerGuid: $guid, filter: $filter) {
                    edges {
                        guid
                        ... on FileFolder {
                            hasChildren
                            title
                            subtype
                            url
                            accessId
                            writeAccessId
                            mimeType
                            __typename
                        }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "guid": self.folder1.guid,
            "filter": "folders"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.folder2.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 1)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 1)

        variables = {
            "guid": self.folder2.guid,
            "filter": "files"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.file.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 1)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 1)


    def test_edit_folder_access_id_recursive(self):

        mutation = """
            mutation editFileFolder($input: editFileFolderInput!) {
            editFileFolder(input: $input) {
                entity {
                guid
                ... on FileFolder {
                    accessId
                    writeAccessId
                    __typename
                }
                __typename
                }
                __typename
            }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "input": {
                "guid": self.folder1.guid,
                "accessId": 1,
                "isAccessRecursive": True
            }
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["editFileFolder"]["entity"]["guid"], self.folder1.guid)
        self.assertEqual(data["editFileFolder"]["entity"]["__typename"], "FileFolder")

        query = """
            query OpenFolder($guid: String, $filter: String) {
                files(containerGuid: $guid, filter: $filter) {
                    edges {
                        guid
                        ... on FileFolder {
                            hasChildren
                            title
                            subtype
                            url
                            accessId
                            writeAccessId
                            mimeType
                            __typename
                        }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "guid": self.folder1.guid,
            "filter": "folders"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.folder2.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 1)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 0)

        variables = {
            "guid": self.folder2.guid,
            "filter": "files"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.file.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 1)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 0)


    def test_edit_folder_write_access_id_recursive(self):

        mutation = """
            mutation editFileFolder($input: editFileFolderInput!) {
            editFileFolder(input: $input) {
                entity {
                guid
                ... on FileFolder {
                    accessId
                    writeAccessId
                    __typename
                }
                __typename
                }
                __typename
            }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "input": {
                "guid": self.folder1.guid,
                "writeAccessId": 1,
                "isAccessRecursive": True
            }
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["editFileFolder"]["entity"]["guid"], self.folder1.guid)
        self.assertEqual(data["editFileFolder"]["entity"]["__typename"], "FileFolder")

        query = """
            query OpenFolder($guid: String, $filter: String) {
                files(containerGuid: $guid, filter: $filter) {
                    edges {
                        guid
                        ... on FileFolder {
                            hasChildren
                            title
                            subtype
                            url
                            accessId
                            writeAccessId
                            mimeType
                            __typename
                        }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "guid": self.folder1.guid,
            "filter": "folders"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.folder2.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 2)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 1)

        variables = {
            "guid": self.folder2.guid,
            "filter": "files"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.file.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 2)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 1)


    def test_edit_folder_access_ids_not_recursive(self):

        mutation = """
            mutation editFileFolder($input: editFileFolderInput!) {
            editFileFolder(input: $input) {
                entity {
                guid
                ... on FileFolder {
                    accessId
                    writeAccessId
                    __typename
                }
                __typename
                }
                __typename
            }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "input": {
                "guid": self.folder1.guid,
                "accessId": 1,
                "writeAccessId": 1,
                "isAccessRecursive": False
            }
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["editFileFolder"]["entity"]["guid"], self.folder1.guid)
        self.assertEqual(data["editFileFolder"]["entity"]["__typename"], "FileFolder")

        query = """
            query OpenFolder($guid: String, $filter: String) {
                files(containerGuid: $guid, filter: $filter) {
                    edges {
                        guid
                        ... on FileFolder {
                            hasChildren
                            title
                            subtype
                            url
                            accessId
                            writeAccessId
                            mimeType
                            __typename
                        }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "guid": self.folder1.guid,
            "filter": "folders"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.folder2.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 2)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 0)

        variables = {
            "guid": self.folder2.guid,
            "filter": "files"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.file.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 2)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 0)


    def test_edit_folder_access_ids_recursive_no_read_access_file(self):

        mutation = """
            mutation editFileFolder($input: editFileFolderInput!) {
            editFileFolder(input: $input) {
                entity {
                guid
                ... on FileFolder {
                    accessId
                    writeAccessId
                    __typename
                }
                __typename
                }
                __typename
            }
            }
        """
        request = HttpRequest()
        request.user = self.user1

        variables = { 
            "input": {
                "guid": self.folder3.guid,
                "accessId": 1,
                "writeAccessId": 1,
                "isAccessRecursive": True
            }
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["editFileFolder"]["entity"]["guid"], self.folder3.guid)
        self.assertEqual(data["editFileFolder"]["entity"]["__typename"], "FileFolder")

        query = """
            query OpenFolder($guid: String, $filter: String) {
                files(containerGuid: $guid, filter: $filter) {
                    edges {
                        guid
                        ... on FileFolder {
                            hasChildren
                            title
                            subtype
                            url
                            accessId
                            writeAccessId
                            mimeType
                            __typename
                        }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "guid": self.folder3.guid,
            "filter": "files"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["files"]["edges"][0]["guid"], self.file2.guid)
        self.assertEqual(data["files"]["edges"][0]["accessId"], 2)
        self.assertEqual(data["files"]["edges"][0]["writeAccessId"], 0)
