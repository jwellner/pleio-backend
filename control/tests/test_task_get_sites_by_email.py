from control.tasks import get_sites_by_email
from tenants.helpers import FastTenantTestCase
from user.factories import UserFactory


class TestTaskGetSitesByEmailTestCase(FastTenantTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_sites_by_email(self):
        result = get_sites_by_email(self.user.email)

        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], {
            "user_name": self.user.name,
            "user_email": self.user.email,
            "user_external_id": self.user.external_id,
            "id": self.tenant.id,
            "schema": self.tenant.schema_name,
            "domain": self.tenant.primary_domain,
        })
