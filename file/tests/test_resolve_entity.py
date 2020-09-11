import json
import os
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone
from core.models import Group
from user.models import User
from file.models import FileFolder
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify
from django.core.files import File
from unittest.mock import MagicMock, patch
from django.conf import settings

class FileFolderTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.folder = FileFolder.objects.create(
            title="images",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_folder=True
        )

        self.query = """
            fragment FileParts on FileFolder {
                title
                subtype
                timeCreated
                timeUpdated
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
                download
                thumbnail
            }
            query GetFile($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...FileParts
                }
            }
        """

    def tearDown(self):
        FileFolder.objects.all().delete()
        self.authenticatedUser.delete()

    @patch("file.models.get_mimetype")
    @patch("{}.save".format(settings.DEFAULT_FILE_STORAGE))
    def test_file(self, mock_save, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_save.return_value = 'test.gif'
        mock_mimetype.return_value = file_mock.content_type

        self.file = FileFolder.objects.create(
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            tags=["tag1", "tag2"],
            upload=file_mock
        )

        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.file.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.file.guid)
        self.assertEqual(data["entity"]["title"], file_mock.name)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.file.created_at))
        self.assertEqual(data["entity"]["tags"], self.file.tags)
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["url"], "/files/view/{}/{}".format(self.file.guid, os.path.basename(self.file.upload.name)))
        self.assertEqual(data["entity"]["parentFolder"], None)
        self.assertEqual(data["entity"]["subtype"], "file")
        self.assertEqual(data["entity"]["hasChildren"], False)
        self.assertEqual(data["entity"]["mimeType"], file_mock.content_type)
        self.assertEqual(data["entity"]["thumbnail"], self.file.thumbnail_url)
        self.assertEqual(data["entity"]["download"], self.file.download_url)

        mock_save.assert_called_once()

    def test_folder(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.folder.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.folder.guid)
        self.assertEqual(data["entity"]["title"], self.folder.title)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.folder.created_at))
        self.assertEqual(data["entity"]["tags"], self.folder.tags)
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["url"], "/user/{}/files/{}".format(self.folder.owner.guid, self.folder.guid))
        self.assertEqual(data["entity"]["parentFolder"], None)
        self.assertEqual(data["entity"]["subtype"], "folder")
        #self.assertEqual(data["entity"]["hasChildren"], True)
        self.assertEqual(data["entity"]["mimeType"], None)

    @patch("file.models.get_mimetype")
    @patch("{}.save".format(settings.DEFAULT_FILE_STORAGE))
    def test_file_in_folder(self, mock_save, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.pdf'
        file_mock.content_type = 'application/pdf'

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

        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.file_in_folder.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.file_in_folder.guid)
        self.assertEqual(data["entity"]["title"], file_mock.name)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.file_in_folder.created_at))
        self.assertEqual(data["entity"]["tags"], self.file_in_folder.tags)
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["url"], "/files/view/{}/{}".format(self.file_in_folder.guid, os.path.basename(self.file_in_folder.upload.name)))
        self.assertEqual(data["entity"]["parentFolder"]["guid"], self.folder.guid)
        self.assertEqual(data["entity"]["subtype"], "file")
        self.assertEqual(data["entity"]["hasChildren"], False)
        self.assertEqual(data["entity"]["mimeType"], file_mock.content_type)

        mock_save.assert_called_once()
