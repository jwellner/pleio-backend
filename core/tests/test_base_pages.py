from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestBasePagesTestCase(PleioTenantTestCase):

    def test_home_page_contains_user_email(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get('/')

        self.assertEqual(200, response.status_code)
        self.assertIn(user.email, response.content.decode())

    def test_superadmin_page_contains_user_email(self):
        admin = AdminFactory(is_superadmin=True)
        self.client.force_login(admin)

        response = self.client.get('/superadmin')

        self.assertEqual(200, response.status_code, msg=response)
        self.assertIn(admin.email, response.content.decode())
