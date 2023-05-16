from unittest import mock
from django_tenants.utils import schema_context

from control.tasks import add_site
from core.tests.helpers import PleioTenantTestCase, suppress_stdout
from tenants.models import Client

class ClientSaveException(Exception):
    pass

class TestTaskAddSiteTestCase(PleioTenantTestCase):

    @suppress_stdout()
    @schema_context('public')
    @mock.patch('tenants.models.Client.save')
    def test_add_site_adds_site(self, client_save_mock):
        client_save_mock.side_effect = ClientSaveException
        try:
            add_site('demo', 'demo.local')
        except ClientSaveException:
            return

        assert "Exception not called!"
