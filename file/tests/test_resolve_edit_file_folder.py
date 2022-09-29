from django.utils import timezone
from django.core.files import File
from django.conf import settings
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from file.helpers.compression import get_download_filename
from user.models import User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from unittest.mock import MagicMock, patch
from ..models import FileFolder


class EditFileFolderTestCase(PleioTenantTestCase):

    def setUp(self):
        super(EditFileFolderTestCase, self).setUp()
        self.authenticatedUser = mixer.blend(User, name="Aut Hen Ticated")
        self.user1 = mixer.blend(User, name="User One")
        self.user2 = mixer.blend(User, name="Someone Else")

        self.PREVIOUS_DESCRIPTION = 'PREVIOUS_DESCRIPTION'
        self.EXPECTED_DESCRIPTION = 'EXPECTED_DESCRIPTION'

        self.group = mixer.blend(Group, owner=self.authenticatedUser)
        self.group.join(self.user1, 'member')
        self.folder1 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.folder2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=self.folder1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.folder3 = FileFolder.objects.create(
            owner=self.user1,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.file = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=False,
            group=self.group,
            parent=self.folder2,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
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
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=None,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.folder2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=self.folder1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file3 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=False,
            group=self.group,
            parent=self.folder2,
            title="a file",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file4 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=False,
            group=self.group,
            parent=self.folder2,
            title="b file",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file5 = FileFolder.objects.create(
            owner=self.user2,
            rich_description=self.PREVIOUS_DESCRIPTION,
            is_folder=False,
            group=self.group,
            parent=self.folder1,
            title="Someone Elses file",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user2.id)]
        )
        self.data = {
            "input": {
                "guid": None,
                "richDescription": self.EXPECTED_DESCRIPTION,
                "title": "",
                "file": "",
                "ownerGuid": "",
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
            }
        }
        self.mutation = """
            fragment FileFolderParts on FileFolder {
                title
                description
                richDescription
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
                group {
                    guid
                }
                owner {
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

    @patch("file.resolvers.mutation.strip_exif")
    @patch("core.lib.get_mimetype")
    @patch("{}.save".format(settings.DEFAULT_FILE_STORAGE))
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_edit_file_title(self, mock_open, mock_save, mock_mimetype, mocked_strip_exif):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'
        file_mock.size = 123

        mock_save.return_value = "test.gif"
        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        test_file = FileFolder.objects.create(
            rich_description=self.PREVIOUS_DESCRIPTION,
            read_access=[ACCESS_TYPE.logged_in],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock
        )

        variables = self.data

        newPublishedTime = timezone.now() + timezone.timedelta(days=-1)

        variables["input"]["guid"] = test_file.guid
        variables["input"]["title"] = "test123.gif"
        variables["input"]["tags"] = ["tag_one", "tag_two"]
        variables["input"]["timePublished"] = newPublishedTime.isoformat()
        variables["input"]["ownerGuid"] = self.user1.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editFileFolder"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["description"], self.EXPECTED_DESCRIPTION)
        self.assertEqual(entity["richDescription"], self.EXPECTED_DESCRIPTION)
        self.assertEqual(entity["mimeType"], test_file.mime_type)
        self.assertEqual(entity["tags"][0], "tag_one")
        self.assertEqual(entity["tags"][1], "tag_two")
        self.assertEqual(entity["owner"]["guid"], self.user1.guid)
        self.assertDateEqual(entity["timePublished"], str(newPublishedTime))
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])
        self.assertTrue(mocked_strip_exif.called)

        test_file.refresh_from_db()
        self.assertEqual(test_file.title, variables['input']['title'])
        self.assertEqual(test_file.tags, variables['input']['tags'])
        self.assertEqual(test_file.published, newPublishedTime)
        self.assertEqual(test_file.owner.guid, self.user1.guid)
        self.assertIn(ACCESS_TYPE.user.format(self.user1.guid), test_file.write_access)

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
        variables = {
            "input": {
                "guid": self.folder1.guid,
                "accessId": 1,
                "writeAccessId": 1,
                "isAccessRecursive": True
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        entity = result["data"]["editFileFolder"]["entity"]
        self.assertEqual(entity["guid"], self.folder1.guid)
        self.assertEqual(entity["__typename"], "FileFolder")

        query = """
            query OpenFolder($guid: String, $filter: String) {
                files(containerGuid: $guid, filter: $filter) {
                    total
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

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["files"]["edges"][0]

        self.assertEqual(entity["guid"], self.folder2.guid)
        self.assertEqual(entity["accessId"], 1)
        self.assertEqual(entity["writeAccessId"], 1)

        variables = {
            "guid": self.folder2.guid,
            "filter": "files",
            "limit": 1
        }

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["files"]["edges"][0]

        self.assertEqual(entity["guid"], self.file3.guid)
        self.assertEqual(entity["accessId"], 1)
        self.assertEqual(entity["writeAccessId"], 1)
        self.assertEqual(result["data"]["files"]["total"], 2)

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

        variables = {
            "input": {
                "guid": self.folder1.guid,
                "accessId": 1,
                "isAccessRecursive": True
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        entity = result["data"]["editFileFolder"]["entity"]
        self.assertEqual(entity["guid"], self.folder1.guid)
        self.assertEqual(entity["__typename"], "FileFolder")

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

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["files"]["edges"][0]

        self.assertEqual(entity["guid"], self.folder2.guid)
        self.assertEqual(entity["accessId"], 1)
        self.assertEqual(entity["writeAccessId"], 0)

        variables = {
            "guid": self.folder2.guid,
            "filter": "files"
        }

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["files"]["edges"][0]

        self.assertEqual(entity["guid"], self.file3.guid)
        self.assertEqual(entity["accessId"], 1)
        self.assertEqual(entity["writeAccessId"], 0)

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
        variables = {
            "input": {
                "guid": self.folder1.guid,
                "writeAccessId": 1,
                "isAccessRecursive": True
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        entity = result["data"]["editFileFolder"]["entity"]
        self.assertEqual(entity["guid"], self.folder1.guid)
        self.assertEqual(entity["__typename"], "FileFolder")

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

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["files"]["edges"][0]

        self.assertEqual(entity["guid"], self.folder2.guid)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["writeAccessId"], 1)

        variables = {
            "guid": self.folder2.guid,
            "filter": "files"
        }

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["files"]["edges"][0]

        self.assertEqual(entity["guid"], self.file3.guid)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["writeAccessId"], 1)

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

        variables = {
            "input": {
                "guid": self.folder1.guid,
                "accessId": 1,
                "writeAccessId": 1,
                "isAccessRecursive": False
            }
        }
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(mutation, variables)

        entity = result["data"]["editFileFolder"]["entity"]
        self.assertEqual(entity["guid"], self.folder1.guid)
        self.assertEqual(entity["__typename"], "FileFolder")

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

        result = self.graphql_client.post(query, variables)

        entity = result["data"]["files"]["edges"][0]
        self.assertEqual(entity["guid"], self.folder2.guid)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["writeAccessId"], 0)

        variables = {
            "guid": self.folder2.guid,
            "filter": "files"
        }

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["files"]["edges"][0]

        self.assertEqual(entity["guid"], self.file3.guid)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["writeAccessId"], 0)

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
        variables = {
            "input": {
                "guid": self.folder3.guid,
                "accessId": 1,
                "writeAccessId": 1,
                "isAccessRecursive": True
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        entity = result["data"]["editFileFolder"]["entity"]
        self.assertEqual(entity["guid"], self.folder3.guid)
        self.assertEqual(entity["__typename"], "FileFolder")

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

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["files"]["edges"][0]

        self.assertEqual(entity["guid"], self.file2.guid)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["writeAccessId"], 0)

    @patch('file.tasks.post_process_file_attributes.delay')
    @patch('file.validators.is_upload_complete')
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_retry_if_not_ok(self, mock_open, mock_is_upload_complete, mock_post_process_file_attributes):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'icon-name.jpg'
        file_mock.title = 'icon-name.jpg'
        file_mock.content_type = 'image/jpeg'
        file_mock.size = 123

        mock_open.return_value = file_mock

        mock_is_upload_complete.return_value = False

        self.file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock,
            title=file_mock.title
        )

        assert mock_post_process_file_attributes.called

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_get_download_filename(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'icon-name.jpg'
        file_mock.title = 'icon-name.jpg'
        file_mock.content_type = 'image/jpeg'
        file_mock.size = 123

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        self.file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock,
            title=file_mock.title
        )

        self.assertEqual(get_download_filename(self.file), 'icon-name.jpg')

        self.file.title = 'iconnewname'
        self.file.save()

        self.assertEqual(get_download_filename(self.file), 'iconnewname.jpg')

        self.file.title = 'iconnewname.txt'
        self.file.save()

        self.assertEqual(get_download_filename(self.file), 'iconnewname.txt.jpg')

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_get_download_filename_csv(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'localfile name'
        file_mock.title = 'csv-name.csv'
        file_mock.content_type = 'text/plain'
        file_mock.size = 123

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        self.file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock,
            title=file_mock.title
        )

        self.assertEqual(get_download_filename(self.file), 'csv-name.csv')

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_get_download_filename_no_mimetype(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'localfile name'
        file_mock.title = 'csv-name.weird'
        file_mock.content_type = None
        file_mock.size = 123

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        self.file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock,
            title=file_mock.title
        )

        self.assertEqual(get_download_filename(self.file), 'csv-name.weird')

    def test_update_ownership_updates_only_current_file_folder(self):
        query = """
        mutation editFileFolder($input: editFileFolderInput!) {
            editFileFolder(input: $input) {
                entity {
                    guid
                }
            }
        }
        """
        variables = {
            "input": {
                "guid": self.folder1.guid,
                "ownerGuid": self.user1.guid,
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        self.graphql_client.post(query, variables)

        expected_access = ACCESS_TYPE.user.format(self.user1.guid)
        for entity, message in (
                (self.folder2, "Folder2 %s access is unexpectedly updated"),
                (self.file3, "File3 %s access is unexpectedly updated"),
                (self.file4, "File4 %s access is unexpectedly updated"),
                (self.file5, "File4 %s access is unexpectedly updated"),
        ):
            entity.refresh_from_db()
            self.assertNotIn(expected_access, entity.write_access, msg=message % 'write')

        self.folder1.refresh_from_db()
        self.assertIn(expected_access, self.folder1.write_access, msg="Folder1 is not updated correctly")

    def test_update_ownership_updates_recursive(self):
        query = """
        mutation editFileFolder($input: editFileFolderInput!) {
            editFileFolder(input: $input) {
                entity {
                    guid
                }
            }
        }
        """
        variables = {
            "input": {
                "guid": self.folder1.guid,
                "ownerGuid": self.user1.guid,
                "ownerGuidRecursive": 'updateAllFiles',
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        self.graphql_client.post(query, variables)

        expected_access = ACCESS_TYPE.user.format(self.user1.guid)
        for entity, message in (
                (self.folder1, "Folder1 %s access is not updated correctly"),
                (self.folder2, "Folder2 %s access is not updated correctly"),
                (self.file3, "File3 %s access is not updated correctly"),
                (self.file4, "File4 %s access is not updated correctly"),
                (self.file5, "File5 %s access is not updated correctly"),
        ):
            entity.refresh_from_db()
            self.assertNotIn(expected_access, entity.read_access, msg=message % 'read')
            self.assertIn(expected_access, entity.write_access, msg=message % 'write')

    def test_update_ownership_updates_recursive_by_owner(self):
        query = """
        mutation editFileFolder($input: editFileFolderInput!) {
            editFileFolder(input: $input) {
                entity {
                    guid
                }
            }
        }
        """
        variables = {
            "input": {
                "guid": self.folder1.guid,
                "ownerGuid": self.user1.guid,
                "ownerGuidRecursive": 'updateOwnerFiles',
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        self.graphql_client.post(query, variables)

        expected_access = ACCESS_TYPE.user.format(self.user1.guid)
        for entity, message in (
                (self.folder1, "Folder1 %s access is not updated correctly"),
                (self.folder2, "Folder2 %s access is not updated correctly"),
                (self.file3, "File3 %s access is not updated correctly"),
                (self.file4, "File4 %s access is not updated correctly"),
        ):
            entity.refresh_from_db()
            self.assertNotIn(expected_access, entity.read_access, msg=message % 'read')
            self.assertIn(expected_access, entity.write_access, msg=message % 'write')

        self.file5.refresh_from_db()
        self.assertNotIn(expected_access, self.file5.write_access, msg="File5 is updated unexpectedly")
