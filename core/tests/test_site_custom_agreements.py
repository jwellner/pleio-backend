import os
from core.models import CustomAgreement
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from mixer.backend.django import mixer

class SiteCustomAgreementsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()

        self.query = """
            query SiteCustomAgreements {
                siteCustomAgreements {
                    name
                    url
                    fileName
                }
            }
        """
        self.customagreement1 =  mixer.blend(CustomAgreement)
        self.customagreement2 =  mixer.blend(CustomAgreement)

    def tearDown(self):
        super().tearDown()

    def test_site_custom_agreements_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]['siteCustomAgreements']
        self.assertEqual(data[0]['name'], self.customagreement1.name)
        self.assertEqual(data[0]['url'], self.customagreement1.url)
        self.assertEqual(data[0]['fileName'], os.path.basename(self.customagreement1.document.name))
        self.assertEqual(data[1]['name'], self.customagreement2.name)
        self.assertEqual(data[1]['url'], self.customagreement2.url)
        self.assertEqual(data[1]['fileName'], os.path.basename(self.customagreement2.document.name))

    def test_site_custom_agreements_by_anonymous(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.query, {})

    def test_site_custom_agreements_by_user(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.query, {})
