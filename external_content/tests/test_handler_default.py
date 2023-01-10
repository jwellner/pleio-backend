from core.tests.helpers import PleioTenantTestCase
from external_content.api_handlers.default import ApiHandler
from external_content.factories import ExternalContentSourceFactory
from external_content.models import ExternalContent


class TestHandlerDefaultTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.source = ExternalContentSourceFactory()
        self.handler = ApiHandler(self.source)

    def tearDown(self):
        self.source.delete()
        ExternalContent.objects.all().delete()

        super().tearDown()

    def test_pull(self):
        self.handler.pull()

        self.assertTrue(ExternalContent.objects.exists())
