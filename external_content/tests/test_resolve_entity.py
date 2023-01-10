from core.tests.helpers import PleioTenantTestCase
from external_content.factories import ExternalContentSourceFactory, ExternalContentFactory
from user.factories import AdminFactory


class TestSingleExternalContentItemTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.override_config(IS_CLOSED=False)
        self.source = ExternalContentSourceFactory()
        self.content = ExternalContentFactory(source=self.source)
        self.query = '''
        query Entity($guid: String) {
            entity(guid: $guid) {
                guid
                status
                ... on ExternalContent {
                    title
                    description
                    timeCreated
                    timeUpdated
                    timePublished
                    canEdit
                    accessId
                    writeAccessId
                    owner {
                        guid
                    }
                    source {
                        key
                        name
                        handlerId
                    }
                    remoteId
                    url
                }
            }
        }
        '''
        self.variables = {
            'guid': self.content.guid
        }

    def tearDown(self):
        self.content.delete()
        self.source.delete()
        super().tearDown()

    def test_entity_properties(self):
        result = self.graphql_client.post(self.query, self.variables)

        entity = result['data']['entity']
        self.assertEqual(entity['guid'], self.content.guid)
        self.assertEqual(entity['status'], 200)
        self.assertEqual(entity['title'], self.content.title)
        self.assertEqual(entity['description'], self.content.description)
        self.assertEqual(entity['timeCreated'], self.content.created_at.isoformat())
        self.assertEqual(entity['timeUpdated'], self.content.updated_at.isoformat())
        self.assertEqual(entity['timePublished'], self.content.published.isoformat())
        self.assertEqual(entity['canEdit'], False)
        self.assertEqual(entity['accessId'], 2)
        self.assertEqual(entity['writeAccessId'], 0)
        self.assertEqual(entity['owner'], {"guid": self.content.owner.guid})
        self.assertEqual(entity['source'], {"key": self.source.guid,
                                            "handlerId": self.source.handler_id,
                                            "name": self.source.name})
        self.assertEqual(entity['remoteId'], self.content.remote_id)
        self.assertEqual(entity['url'], self.content.canonical_url)
