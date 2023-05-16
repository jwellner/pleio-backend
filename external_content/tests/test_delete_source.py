from core.tests.helpers import PleioTenantTestCase
from external_content.factories import ExternalContentSourceFactory, ExternalContentFactory
from external_content.models import ExternalContentSource, ExternalContent
from user.factories import AdminFactory, UserFactory


class TestDeleteSourceTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.authenticated_user = UserFactory()
        self.admin_user = AdminFactory()

        self.source1 = ExternalContentSourceFactory()
        self.source2 = ExternalContentSourceFactory()
        self.source3 = ExternalContentSourceFactory()

        self.article1 = ExternalContentFactory(source=self.source1)
        self.article2 = ExternalContentFactory(source=self.source1)
        self.article3 = ExternalContentFactory(source=self.source1)
        self.source2article = ExternalContentFactory(source=self.source2)

        self.mutation = """
        mutation DeleteSource($key: String!) {
            payload: deleteExternalContentSource(key: $key) {
                edges {
                    key
                    name
                    pluralName
                    handlerId
                }
            }
        }
        """
        self.variables = {
            "key": self.source1.guid
        }

    def tearDown(self):
        super().tearDown()

    def test_anonymous_delete_source(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_authenticated_delete_source(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.authenticated_user)
            self.graphql_client.post(self.mutation, self.variables)

    def test_admin_delete_source(self):
        self.graphql_client.force_login(self.admin_user)
        result = self.graphql_client.post(self.mutation, self.variables)

        # Expect the other sources as a result.
        result_index = {e['key']: e for e in result['data']['payload']['edges']}
        expected_index = {e.guid: {
            'key': e.guid,
            'name': e.name,
            'pluralName': e.plural_name,
            'handlerId': e.handler_id,
        } for e in [self.source2, self.source3]}
        self.assertDictEqual(result_index, expected_index)

        # Expect only the source1 content to be deleted.
        self.assertEqual([self.source2article], [c for c in ExternalContent.objects.all()])
