from core.tests.helpers import PleioTenantTestCase
from external_content.factories import ExternalContentSourceFactory
from external_content.models import ExternalContentSource
from user.factories import AdminFactory, UserFactory


class TestAddDatahubSourceTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.authenticated_visitor = UserFactory()

        self.mutation = """
        mutation AddSource ($input: AddDatahubContentSourceInput!) {
            payload: addDatahubExternalContentSource(input: $input) {
                edges {
                    key
                    name
                    pluralName
                    handlerId
                    ... on DatahubContentSource {
                        apiUrl
                        frontendUrl
                        batchSize
                    }
                }
            }
        }
        """
        self.variables = {
            'input': {
                'name': 'Datahub resource',
                'pluralName': 'Datahub resources',
                'apiUrl': 'https://test.datahub.pleio.wonderbit.com/api/v1/',
                'frontendUrl': 'https://test.datahub.pleio.wonderbit.com/en/explorer/',
                'batchSize': 50,
            }
        }

    def tearDown(self):
        self.admin.delete()
        self.authenticated_visitor.delete()
        ExternalContentSource.objects.all().delete()

        super().tearDown()

    def test_anonymous_add_datahub_source(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_authenticated_add_datahub_source(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.authenticated_visitor)
            self.graphql_client.post(self.mutation, self.variables)

    def test_admin_add_datahub_source(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)

        source = ExternalContentSource.objects.first()

        self.assertDictEqual(result['data']['payload'], {
            'edges': [{"key": source.guid,
                       "handlerId": source.handler_id,
                       "name": self.variables['input']['name'],
                       "pluralName": self.variables['input']['pluralName'],
                       "apiUrl": self.variables['input']['apiUrl'],
                       "frontendUrl": self.variables['input']['frontendUrl'],
                       "batchSize": self.variables['input']['batchSize']}]
        })


class TestUpdateDatahubSourceTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.authenticated_visitor = UserFactory()
        self.source = ExternalContentSourceFactory()

        self.mutation = """
        mutation EditSource ($input: UpdateDatahubContentSourceInput!) {
            payload: editDatahubExternalContentSource(input: $input) {
                edges {
                    key
                    name
                    pluralName
                    handlerId
                    ... on DatahubContentSource {
                        apiUrl
                        frontendUrl
                        batchSize
                    }
                }
            }
        }
        """
        self.variables = {
            'input': {
                'key': self.source.guid,
                'name': 'Demo',
                'pluralName': 'Demos',
                'apiUrl': 'https://pleio.com/',
                'frontendUrl': 'https://rvo-frontend.gov/en/explorer/',
                'batchSize': 50
            }
        }

    def tearDown(self):
        self.source.delete()
        super().tearDown()

    def test_anonymous_update_datahub_source(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_authenticated_update_datahub_source(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.authenticated_visitor)
            self.graphql_client.post(self.mutation, self.variables)

    def test_admin_update_datahub_source(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)

        self.source.refresh_from_db()
        self.assertDictEqual(result['data']['payload'], {
            'edges': [{"key": self.variables['input']['key'],
                       "handlerId": self.source.handler_id,
                       "name": self.variables['input']['name'],
                       "pluralName": self.variables['input']['pluralName'],
                       "apiUrl": self.variables['input']['apiUrl'],
                       "frontendUrl": self.variables['input']['frontendUrl'],
                       "batchSize": 50}]
        })
