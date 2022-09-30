import os
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from file.models import FileFolder
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.core.files import File
from unittest.mock import MagicMock, patch
from django.conf import settings


class FileFolderTestCase(PleioTenantTestCase):

    def setUp(self):
        super(FileFolderTestCase, self).setUp()
        self.authenticatedUser = mixer.blend(User)

        self.folder = FileFolder.objects.create(
            title="images",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            type=FileFolder.Types.FOLDER,
        )

        self.query = """
            query GetFile($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ... on File {
                        title
                        subtype
                        timeCreated
                        timeUpdated
                        timePublished
                        scheduleArchiveEntity
                        scheduleDeleteEntity
                        accessId
                        writeAccessId
                        canEdit
                        tags
                        url
                        inGroup
                        parentFolder {
                            guid
                        }
                        group {
                            guid
                        }
                        hasChildren
                        mimeType
                        thumbnail
                        download
                    }
                    ... on Folder {
                        title
                        subtype
                        timeCreated
                        timeUpdated
                        timePublished
                        scheduleArchiveEntity
                        scheduleDeleteEntity
                        accessId
                        writeAccessId
                        canEdit
                        tags
                        url
                        inGroup
                        parentFolder {
                            guid
                        }
                        group {
                            guid
                        }
                        hasChildren
                    }
                }
            }
        """

    def tearDown(self):
        FileFolder.objects.all().delete()
        self.authenticatedUser.delete()

    @patch("core.lib.get_mimetype")
    @patch("{}.save".format(settings.DEFAULT_FILE_STORAGE))
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_file(self, mock_open, mock_save, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'
        file_mock.size = 123

        mock_open.return_value = file_mock
        mock_save.return_value = 'test.gif'
        mock_mimetype.return_value = file_mock.content_type

        self.file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock
        )

        variables = {
            "guid": self.file.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], self.file.guid)
        self.assertEqual(entity["title"], file_mock.name)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.file.created_at.isoformat())
        self.assertEqual(entity["tags"], self.file.tags)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/files/view/{}/{}".format(self.file.guid, os.path.basename(self.file.upload.name)))
        self.assertEqual(entity["parentFolder"], None)
        self.assertEqual(entity["subtype"], "file")
        self.assertEqual(entity["hasChildren"], False)
        self.assertEqual(entity["mimeType"], file_mock.content_type)
        self.assertEqual(entity["thumbnail"], self.file.thumbnail_url)
        self.assertEqual(entity["download"], self.file.download_url)
        self.assertIsNotNone(entity["timePublished"])
        self.assertIsNone(entity["scheduleArchiveEntity"])
        self.assertIsNone(entity["scheduleDeleteEntity"])

        mock_save.assert_called_once()

    def test_folder(self):
        variables = {
            "guid": self.folder.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.folder.guid)
        self.assertEqual(entity["title"], self.folder.title)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.folder.created_at.isoformat())
        self.assertEqual(entity["tags"], self.folder.tags)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/user/{}/files/{}".format(self.folder.owner.guid, self.folder.guid))
        self.assertEqual(entity["parentFolder"], None)
        self.assertEqual(entity["subtype"], "folder")
        #self.assertEqual(entity["hasChildren"], True)
        #self.assertEqual(entity["mimeType"], None)

    @patch("core.lib.get_mimetype")
    @patch("{}.save".format(settings.DEFAULT_FILE_STORAGE))
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_file_in_folder(self, mock_open, mock_save, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.pdf'
        file_mock.content_type = 'application/pdf'
        file_mock.size = 123

        mock_open.return_value = file_mock
        mock_save.return_value = 'test.pdf'
        mock_mimetype.return_value = file_mock.content_type

        self.file_in_folder = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock,
            parent=self.folder
        )
        variables = {
            "guid": self.file_in_folder.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], self.file_in_folder.guid)
        self.assertEqual(entity["title"], file_mock.name)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.file_in_folder.created_at.isoformat())
        self.assertEqual(entity["tags"], self.file_in_folder.tags)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/files/view/{}/{}".format(self.file_in_folder.guid, os.path.basename(self.file_in_folder.upload.name)))
        self.assertEqual(entity["parentFolder"]["guid"], self.folder.guid)
        self.assertEqual(entity["subtype"], "file")
        self.assertEqual(entity["hasChildren"], False)
        self.assertEqual(entity["mimeType"], file_mock.content_type)

        mock_save.assert_called_once()

    @patch("core.lib.get_mimetype")
    @patch("{}.save".format(settings.DEFAULT_FILE_STORAGE))
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_file_access(self, mock_open, mock_save, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'
        file_mock.size = 123

        mock_save.return_value = 'test.gif'
        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        self.file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.logged_in],
            write_access=[ACCESS_TYPE.logged_in],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock
        )

        variables = {
            "guid": self.file.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], self.file.guid)
        self.assertEqual(entity["title"], file_mock.name)
        self.assertEqual(entity["accessId"], 1)
        self.assertEqual(entity["writeAccessId"], 1)

        mock_save.assert_called_once()

    def test_folder_access(self):
        folder = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.logged_in],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            type=FileFolder.Types.FOLDER,
        )

        variables = {
            "guid": folder.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)
        entity = result["data"]["entity"]

        self.assertEqual(entity["guid"], folder.guid)
        self.assertEqual(entity["title"], folder.title)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["writeAccessId"], 1)
