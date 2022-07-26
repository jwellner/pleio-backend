from django_tenants.utils import schema_context

from control.tasks import add_site
from core.tests.helpers import suppress_stdout
from tenants.helpers import FastTenantTestCase
from tenants.models import Client


class TestTaskAddSiteTestCase(FastTenantTestCase):

    @suppress_stdout()
    @schema_context('public')
    def test_add_site_adds_site(self):
        add_site('demo', 'demo.local')

        assert Client.objects.filter(schema_name='demo').exists()