from django_tenants.test.cases import FastTenantTestCase
from django.core.files import File
from django.conf import settings
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from file.models import FileFolder
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from unittest.mock import MagicMock, patch

class AddFileTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedUser2 = mixer.blend(User)
        self.authenticatedUser3 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')
        self.group.join(self.authenticatedUser3, 'member')

        self.folder = FileFolder.objects.create(
            title="images",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_folder=True,
            group=self.group
        )

        self.EXPECTED_DESCRIPTION = 'EXPECTED_DESCRIPTION'
        self.data = {
            "input": {
                "richDescription": self.EXPECTED_DESCRIPTION,
                "containerGuid": self.group.guid,
                "file": "test.gif",
                "tags": ["tag_one", "tag_two"]
            }
        }
        self.mutation = """
            fragment FileFolderParts on FileFolder {
                title
                description
                richDescription
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

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_file(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addFile"]["entity"]["title"], file_mock.name)
        self.assertEqual(data["addFile"]["entity"]["mimeType"], file_mock.content_type)
        self.assertEqual(data["addFile"]["entity"]["description"], self.EXPECTED_DESCRIPTION)
        self.assertEqual(data["addFile"]["entity"]["richDescription"], self.EXPECTED_DESCRIPTION)
        self.assertEqual(data["addFile"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["addFile"]["entity"]["tags"][0], "tag_one")
        self.assertEqual(data["addFile"]["entity"]["tags"][1], "tag_two")

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_file_not_writable_group(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser2

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "NOT_GROUP_MEMBER")


    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_file_not_writable_folder(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = {
            "input": {
                "containerGuid": self.folder.guid,
                "file": "test.gif",
                "tags": ["tag_one", "tag_two"]
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser3

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_folder_not_writable_group(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        mutation = """
            mutation addFolder($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                __typename
                }
            }
        """
        variables = {
            "input": {
                "containerGuid": self.group.guid,
                "subtype": "folder",
                "title": "testfolder",
                "accessId": 1,
                "writeAccessId": 0,
                "type": "object"
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser2

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "NOT_GROUP_MEMBER")



    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_folder_not_writable_folder(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        mutation = """
            mutation addFolder($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                __typename
                }
            }
        """
        variables = {
            "input": {
                "containerGuid": self.folder.guid,
                "subtype": "folder",
                "title": "testfolder",
                "accessId": 1,
                "writeAccessId": 0,
                "type": "object"
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser3

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_folder(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        mutation = """
            mutation addFolder($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                        guid
                        ...on FileFolder {
                            title
                        }
                        __typename
                    }
                __typename
                }
            }
        """
        variables = {
            "input": {
                "containerGuid": self.group.guid,
                "subtype": "folder",
                "title": "testfolder",
                "accessId": 1,
                "writeAccessId": 0,
                "type": "object"
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser3

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], "testfolder")

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_personal_file(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = self.data
        variables["input"]["containerGuid"] = self.authenticatedUser.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addFile"]["entity"]["title"], file_mock.name)
        self.assertEqual(data["addFile"]["entity"]["mimeType"], file_mock.content_type)
        self.assertEqual(data["addFile"]["entity"]["group"], None)
        self.assertEqual(data["addFile"]["entity"]["tags"][0], "tag_one")
        self.assertEqual(data["addFile"]["entity"]["tags"][1], "tag_two")
