from core.lib import get_entity_filters, get_activity_filters
from core.tests.helpers import PleioTenantTestCase
from external_content.factories import ExternalContentSourceFactory


class TestContentTypeFiltersTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.source = ExternalContentSourceFactory()

    def tearDown(self):
        self.source.delete()
        super().tearDown()

    def test_get_entity_filters(self):
        content_types = get_entity_filters()
        self.assertIn(self.source.guid, [f['key'] for f in content_types])

    def test_get_activity_filters(self):
        content_types = get_activity_filters()
        self.assertNotIn(self.source.guid, [f['key'] for f in content_types])
