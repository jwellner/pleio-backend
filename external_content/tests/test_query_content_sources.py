from core.tests.helpers import PleioTenantTestCase
from external_content.factories import ExternalContentSourceFactory
from user.factories import AdminFactory


class TestQueryContentSourcesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.source = ExternalContentSourceFactory()
        self.admin = AdminFactory()
        self.query = """
        query GetExternalContentSources($handler: ExternalContentSourceHandlerEnum!) {
            externalContentSources(handler: $handler) {
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
            'handler': 'default',
        }

    def tearDown(self):
        super().tearDown()

    def test_get_external_source(self):
        self.graphql_client.force_login(self.admin)
        response = self.graphql_client.post(self.query, self.variables)
        edges = response['data']['externalContentSources']['edges']
        self.assertEqual(edges[0]['key'], self.source.guid)
        self.assertEqual(edges[0]['name'], self.source.name)
        self.assertEqual(edges[0]['pluralName'], self.source.plural_name)
        self.assertEqual(edges[0]['handlerId'], self.source.handler_id)
