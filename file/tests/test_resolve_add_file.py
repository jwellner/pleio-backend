import json

from django.core.files import File
from django.conf import settings
from core.models import Group
from core.constances import USER_NOT_MEMBER_OF_GROUP
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from file.models import FileFolder
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from unittest.mock import MagicMock, patch


class AddFileTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddFileTestCase, self).setUp()
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

        self.RICH_DESCRIPTION = json.dumps({
            'type': 'doc',
            'content': [{
                'type': "paragraph",
                'content': [{
                    'type': 'text',
                    'text': 'expected text',
                }]
            }]
        })
        self.DESCRIPTION = 'expected text\n\n'

        self.data = {
            "input": {
                "richDescription": self.RICH_DESCRIPTION,
                "containerGuid": self.group.guid,
                "file": "test.gif",
                "tags": ["tag_one", "tag_two"],
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

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]['addFile']['entity']
        self.assertEqual(entity["title"], file_mock.name)
        self.assertEqual(entity["mimeType"], file_mock.content_type)
        self.assertEqual(entity["description"], self.DESCRIPTION)
        self.assertEqual(entity["richDescription"], self.RICH_DESCRIPTION)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["tags"][0], "tag_one")
        self.assertEqual(entity["tags"][1], "tag_two")

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_file_not_writable_group(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser2)
        with self.assertGraphQlError(USER_NOT_MEMBER_OF_GROUP):
            self.graphql_client.post(self.mutation, variables)

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

        self.graphql_client.force_login(self.authenticatedUser3)
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.post(self.mutation, variables)

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

        self.graphql_client.force_login(self.authenticatedUser2)
        with self.assertGraphQlError(USER_NOT_MEMBER_OF_GROUP):
            self.graphql_client.post(mutation, variables)

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

        self.graphql_client.force_login(self.authenticatedUser3)
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.post(mutation, variables)

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

        self.graphql_client.force_login(self.authenticatedUser3)
        result = self.graphql_client.post(mutation, variables)

        self.assertEqual(result["data"]["addEntity"]["entity"]["title"], "testfolder")

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

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addFile"]["entity"]
        self.assertEqual(entity["title"], file_mock.name)
        self.assertEqual(entity["mimeType"], file_mock.content_type)
        self.assertEqual(entity["group"], None)
        self.assertEqual(entity["tags"][0], "tag_one")
        self.assertEqual(entity["tags"][1], "tag_two")
