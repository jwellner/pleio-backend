from django.core.files.base import ContentFile

from core.tests.helpers import PleioTenantTestCase
from file.factories import FileFactory, FolderFactory, PadFactory
from file.models import FileFolder
from user.factories import UserFactory


class TestEntitiesFiles(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        file_content = ContentFile("Test123!", "test.txt")
        self.owner = UserFactory()
        self.file1 = FileFactory(owner=self.owner,
                                 upload=file_content)
        self.file2 = FileFactory(owner=self.owner,
                                 upload=file_content)
        self.file3 = FileFactory(owner=self.owner,
                                 upload=file_content)
        self.folder1 = FolderFactory(owner=self.owner)
        self.folder2 = FolderFactory(owner=self.owner)
        self.pad1 = PadFactory(owner=self.owner)

        self.query = """
        query GetFiles($subtype: String) {
            entities(subtype: $subtype) {
                edges {
                    guid
                }
            }
        }
        """

    def tearDown(self):
        self.owner.delete()

        super().tearDown()

    def test_query_all(self):
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, {})

        found_guids = {e['guid'] for e in result['data']['entities']['edges']}
        all_guids = {s.guid for s in FileFolder.objects.all()}

        self.assertEqual(len(found_guids), 6)

        # Test if the set of guids equals the guids from the database
        self.assertEqual(found_guids & all_guids, all_guids)

    def test_query_files(self):
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, {'subtype': 'file'})

        found_guids = {e['guid'] for e in result['data']['entities']['edges']}
        file_guids = {self.file1.guid, self.file2.guid, self.file3.guid}

        self.assertEqual(len(found_guids), 3)
        self.assertEqual(found_guids & file_guids, file_guids)

    def test_query_pads(self):
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, {'subtype': 'pad'})

        found_guids = {e['guid'] for e in result['data']['entities']['edges']}
        pad_guids = {self.pad1.guid}

        self.assertEqual(len(found_guids), 1)
        self.assertEqual(found_guids & pad_guids, pad_guids)

    def test_query_folders(self):
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, {'subtype': 'folder'})

        found_guids = {e['guid'] for e in result['data']['entities']['edges']}
        folder_guids = {self.folder1.guid, self.folder2.guid}

        self.assertEqual(len(found_guids), 2)
        self.assertEqual(found_guids & folder_guids, folder_guids)
