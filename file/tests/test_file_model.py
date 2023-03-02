from unittest import mock

from django.core.files.base import ContentFile

from core.tests.helpers import PleioTenantTestCase
from file.factories import FileFactory, FolderFactory, PadFactory
from file.models import FileFolder
from user.factories import UserFactory
from user.models import User


class Base:
    class TestFileModelTestCaseBase(PleioTenantTestCase):
        owner: User = None

        TITLE = "Demo blog"
        CONTENT = "Demo content"

        def setUp(self):
            super().setUp()

            self.owner = UserFactory()
            self.folder = FolderFactory(owner=self.owner)
            self.entity = self.file_entity_factory(owner=self.owner,
                                                   parent=self.folder,
                                                   title=self.TITLE,
                                                   rich_description=self.CONTENT)

        def tearDown(self):
            self.entity.delete()
            self.owner.delete()
            self.folder.delete()

            super().tearDown()

        def file_entity_factory(self, **kwargs) -> FileFolder:
            raise NotImplementedError()

        @mock.patch("core.models.Entity.serialize")
        def test_serialize(self, serialize):
            serialize.return_value = {}

            self.assertEqual(self.entity.serialize(), {
                "file": None,
                "mimeType": None,
                "parentGuid": self.folder.guid,
                "richDescription": self.CONTENT,
                "size": 0,
                "title": self.TITLE,
            })

        def test_map_rich_text_fields(self):
            before = self.entity.serialize()
            expected = self.entity.serialize()
            expected['richDescription'] = f"new {self.CONTENT}"

            self.entity.map_rich_text_fields(lambda v: "new %s" % v)
            after = self.entity.serialize()

            self.assertNotEqual(after, before)
            self.assertEqual(after, expected)


class TestDiskFileModelTestCase(Base.TestFileModelTestCaseBase):

    def file_entity_factory(self, **kwargs):
        kwargs['upload'] = ContentFile("Abcdefghijklmnopqrstuvwxyz", "demo.txt")
        return FileFactory(**kwargs)

    @mock.patch("core.models.Entity.serialize")
    def test_serialize(self, serialize):
        serialize.return_value = {}

        self.assertEqual(self.entity.serialize(), {
            "file": self.entity.upload.name,
            "mimeType": "text/plain",
            "parentGuid": self.folder.guid,
            "richDescription": self.CONTENT,
            "size": 26,
            "title": self.TITLE,
        })

    def test_is_file(self):
        self.assertTrue(self.entity.is_file())


class TestFolderFileModelTestCase(Base.TestFileModelTestCaseBase):

    def file_entity_factory(self, **kwargs):
        return FolderFactory(**kwargs)

    def test_is_not_a_file(self):
        self.assertFalse(self.entity.is_file())


class TestPadFileModelTestCase(Base.TestFileModelTestCaseBase):

    def file_entity_factory(self, **kwargs):
        return PadFactory(**kwargs)

    def test_is_not_a_file(self):
        self.assertFalse(self.entity.is_file())
