from django.core.files.base import ContentFile

from blog.factories import BlogFactory
from core.tests.helpers import PleioTenantTestCase
from file.factories import FileFactory
from file.models import FileReference
from user.factories import UserFactory


class TestDeleteFileTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.file = FileFactory(owner=self.owner,
                                upload=ContentFile("Test!\n", "testfile.txt"))

        self.mutation = """
        mutation DeleteFile($input: deleteEntityInput!) {
            deleteEntity(input: $input) {
                success
            }
        }
        """
        self.variables = {
            'input': {
                'guid': self.file.guid,
            }
        }

    def tearDown(self):
        self.file.delete()
        self.owner.delete()
        super().tearDown()

    def test_delete_file_without_references(self):
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, self.variables)

        self.assertEqual(result['data']['deleteEntity']['success'], True)

    def test_delete_file_with_profile_relation(self):
        self.file.persist_file()

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, self.variables)

        self.assertEqual(result['data']['deleteEntity']['success'], True)

    def test_delete_file_with_article_relation(self):
        blog = BlogFactory(owner=self.owner)
        FileReference.objects.get_or_create(file=self.file, container=blog)

        with self.assertGraphQlError('file_has_references'):
            self.graphql_client.force_login(self.owner)
            result = self.graphql_client.post(self.mutation, self.variables)

    def test_force_delete_file_with_article_relation(self):
        blog = BlogFactory(owner=self.owner)
        FileReference.objects.get_or_create(file=self.file, container=blog)
        self.variables['input']['force'] = True

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, self.variables)

        self.assertEqual(result['data']['deleteEntity']['success'], True)
