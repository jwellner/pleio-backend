from core.tests.helpers import PleioTenantTestCase
from tenants.models import Agreement, AgreementVersion
from user.models import User

from mixer.backend.django import mixer


class SiteAgreementsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = mixer.blend(User, roles=[], is_delete_requested=False)
        self.admin = mixer.blend(User, roles=['ADMIN'], is_delete_requested=False)

        self.agreement = mixer.blend(Agreement, name="Agreement", description="Agreement description")

        self.version1 = mixer.blend(AgreementVersion, agreement=self.agreement, version="1.0")
        self.version2 = mixer.blend(AgreementVersion, agreement=self.agreement, version="1.1")

        self.query = """
            query SiteAgreements {
                siteAgreements {
                    id
                    name
                    description
                    accepted
                    versions {
                        id
                        version
                        document
                        accepted
                        acceptedBy
                        acceptedDate
                    }
                }
            }
        """

        self.mutation = """
            mutation signSiteAgreementVersion($input: signSiteAgreementVersionInput!) {
                signSiteAgreementVersion(input: $input) {
                    siteAgreementVersion {
                        id
                        version
                        document
                        accepted
                        acceptedBy
                        acceptedDate
                    }
                }
            }
        """

    def test_by_user(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.query, {})

    def test_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(len(data["siteAgreements"]), 1)
        self.assertEqual(data["siteAgreements"][0]["name"], "Agreement")
        self.assertEqual(data["siteAgreements"][0]["description"], "Agreement description")
        self.assertEqual(data["siteAgreements"][0]["accepted"], False)
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["version"], "1.1")
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["accepted"], False)
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["document"], "/agreement/agreement-1-1")
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["version"], "1.0")
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["accepted"], False)
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["document"], "/agreement/agreement-1-0")

    def test_fail_accept_by_admin(self):
        variables = {
            "input": {
                "id": str(self.version1.id),
                "accept": False
            }
        }

        with self.assertGraphQlError("not_accepted"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, variables)

    def test_accept_by_admin(self):
        variables = {
            "input": {
                "id": str(self.version1.id),
                "accept": True
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["signSiteAgreementVersion"]["siteAgreementVersion"]["version"], "1.0")
        self.assertEqual(data["signSiteAgreementVersion"]["siteAgreementVersion"]["accepted"], True)

        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(len(data["siteAgreements"]), 1)
        self.assertEqual(data["siteAgreements"][0]["name"], "Agreement")
        self.assertEqual(data["siteAgreements"][0]["description"], "Agreement description")
        self.assertEqual(data["siteAgreements"][0]["accepted"], False)
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["version"], "1.1")
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["accepted"], False)
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["version"], "1.0")
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["accepted"], True)

        variables = {
            "input": {
                "id": str(self.version2.id),
                "accept": True
            }
        }
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["signSiteAgreementVersion"]["siteAgreementVersion"]["version"], "1.1")
        self.assertEqual(data["signSiteAgreementVersion"]["siteAgreementVersion"]["accepted"], True)

        result = self.graphql_client.post(self.query, {})

        data = result["data"]
        self.assertEqual(len(data["siteAgreements"]), 1)
        self.assertEqual(data["siteAgreements"][0]["name"], "Agreement")
        self.assertEqual(data["siteAgreements"][0]["description"], "Agreement description")
        self.assertEqual(data["siteAgreements"][0]["accepted"], True)
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["version"], "1.1")
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["accepted"], True)
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["version"], "1.0")
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["accepted"], True)
