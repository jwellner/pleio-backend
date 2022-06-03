from http import HTTPStatus
import io
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django.core.cache import cache
from django.db import connection
from ..models import FileFolder
from core.models import Group
from user.models import User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from django.core.files.uploadedfile import SimpleUploadedFile
from zipfile import ZipFile

class DownloadFiles(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.c = TenantClient(self.tenant)
        self.authenticatedUser = mixer.blend(User, name="Aut Hen Ticated")

        self.PREVIOUS_DESCRIPTION = 'PREVIOUS_DESCRIPTION'
        self.EXPECTED_DESCRIPTION = 'EXPECTED_DESCRIPTION'

        self.group = mixer.blend(Group, owner=self.authenticatedUser)
        self.group.join(self.authenticatedUser, 'member')
        self.folder1 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=None,
            title="folder1",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.folder2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=None,
            is_folder=True,
            group=self.group,
            parent=None,
            title="folder2",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        csv_bytes = (
            b'raap;row-1-2@example.com;row-1-3;row-1-4;row-1-5\n'
        )
        upload = SimpleUploadedFile('test.csv', csv_bytes)

        self.file = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=upload,
            is_folder=False,
            group=self.group,
            parent=self.folder1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.file2 = FileFolder.objects.create(
            owner=self.authenticatedUser,
            rich_description=self.PREVIOUS_DESCRIPTION,
            upload=upload,
            is_folder=False,
            group=self.group,
            parent=self.folder2,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

    def test_bulk_download(self):

        path = '/bulk_download?folder_guids[]=' + str(self.folder1.id) + '&folder_guids[]=' + str(self.folder2.id)
        self.c.force_login(self.authenticatedUser)
        response = self.c.get(path)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        zip_file = io.BytesIO(b''.join(response.streaming_content))

        with ZipFile(zip_file, 'r') as zip:
            names = zip.namelist()
            self.assertEqual(names[0], 'folder1/test.csv')
            self.assertEqual(names[1], 'folder2/test.csv')
            

    def test_bulk_download_anonymous(self):

        path = '/bulk_download?folder_guids[]=' + str(self.folder1.id) + '&folder_guids[]=' + str(self.folder2.id)
        response = self.c.get(path)

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
