from mixer.backend.django import mixer
from core.models import Revision
from blog.models import Blog
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from core.constances import ACCESS_TYPE


class TestUpdateRevisionTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.authenticatedUser = UserFactory()
        self.otherUser = UserFactory()
        self.blog: Blog = Blog.objects.create(title="Test public event",
                                              rich_description="JSON to string",
                                              read_access=[ACCESS_TYPE.public],
                                              write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
                                              owner=self.authenticatedUser)
        self.revision1: Revision = mixer.blend(Revision,
                                               _container=self.blog,
                                               content={"richDescription": "Content1"},
                                               description="Version 1")

        self.mutation = """
            mutation ($input: updateRevisionInput!) {
                updateRevision(input: $input) {
                    guid
                    description
                }
            }
        """
        self.variables = {
            "input": {
                "guid": self.revision1.guid,
                "description": "Other description",
            },
        }

    def test_update_revision(self):
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, self.variables)
        revision = result['data']['updateRevision']

        self.assertEqual(revision['guid'], self.variables['input']['guid'])
        self.assertEqual(revision['description'], self.variables['input']['description'])

    def test_update_revision_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_update_revision_other_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.otherUser)
            self.graphql_client.post(self.mutation, self.variables)
