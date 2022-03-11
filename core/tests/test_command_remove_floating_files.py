import os
from unittest import mock

from django.conf import settings
from django.core.files.base import ContentFile
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from core.management.commands.remove_floating_files import Command
from core.models import Attachment
from file.models import FileFolder

class RemoveFloatingFilesTestCase(FastTenantTestCase):

    def setUp(self):
        self.command = Command()
        self.command.stdout = mock.Mock()
        self.fake_tenant = 'no-tenant'
        os.makedirs(os.path.join(settings.MEDIA_ROOT, self.fake_tenant),  exist_ok=True)

    def tearDown(self):
        os.system(f"rm -r {os.path.join(settings.MEDIA_ROOT, self.fake_tenant)}")

    def get_file_path(self, schema_name, filename):
        return os.path.join(settings.MEDIA_ROOT, schema_name, filename)

    def test_removes_floating_file(self):
        path = self.get_file_path(self.tenant.schema_name, 'floating.txt')
        with open(path, 'w+'):
            pass

        self.command.handle()

        self.assertFalse(os.path.exists(path), 'Floating files inside tenant media folder should be deleted')

    def test_keeps_file_outside_tenant(self):
        path = self.get_file_path(self.fake_tenant, 'floating.txt')
        with open(path, 'w+'):
            pass

        self.command.handle()

        self.assertTrue(os.path.exists(path), 'Files outside of tenant media folder should not be deleted')

    def test_keeps_file_for_attachment(self):
        attachment = mixer.blend(Attachment)
        attachment.upload.save('attached.txt', ContentFile(''))
        path = attachment.upload.path

        self.command.handle()

        self.assertTrue(os.path.exists(path), 'Files attached to an attachment should not be deleted')

    def test_keeps_file_for_filefolder(self):
        filefolder = mixer.blend(FileFolder)
        filefolder.upload.save('attached.txt', ContentFile(''))
        path = filefolder.upload.path

        self.command.handle()

        self.assertTrue(os.path.exists(path), 'Files attached to a filefolder should not be deleted')
