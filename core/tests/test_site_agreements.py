from django.db import connection
from django_tenants.test.client import TenantClient
from django_tenants.test.cases import FastTenantTestCase
from tenants.models import Agreement, AgreementAccept, AgreementVersion
from user.models import User

from backend2.schema import schema
from ariadne import graphql_sync
from core.tasks import save_db_disk_usage,save_file_disk_usage
from django.http import HttpRequest
from mixer.backend.django import mixer
from django.core.files.uploadedfile import SimpleUploadedFile


class SiteAgreementsTestCase(FastTenantTestCase):

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

    def tearDown(self):
        pass

    def test_by_user(self):
        request = HttpRequest()
        request.user = self.user

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")

    def test_by_admin(self):

        request = HttpRequest()
        request.user = self.admin

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

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

        request = HttpRequest()
        request.user = self.admin

        variables = {
            "input": {
                "id": str(self.version1.id),
                "accept": False
            }
        }

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_accepted")


    def test_accept_by_admin(self):

        request = HttpRequest()
        request.user = self.admin

        variables = {
            "input": {
                "id": str(self.version1.id),
                "accept": True
            }
        }

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["signSiteAgreementVersion"]["siteAgreementVersion"]["version"], "1.0")
        self.assertEqual(data["signSiteAgreementVersion"]["siteAgreementVersion"]["accepted"], True)

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

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

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["signSiteAgreementVersion"]["siteAgreementVersion"]["version"], "1.1")
        self.assertEqual(data["signSiteAgreementVersion"]["siteAgreementVersion"]["accepted"], True)

        variables = {
        }

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(len(data["siteAgreements"]), 1)
        self.assertEqual(data["siteAgreements"][0]["name"], "Agreement")
        self.assertEqual(data["siteAgreements"][0]["description"], "Agreement description")
        self.assertEqual(data["siteAgreements"][0]["accepted"], True)
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["version"], "1.1")
        self.assertEqual(data["siteAgreements"][0]["versions"][0]["accepted"], True)
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["version"], "1.0")
        self.assertEqual(data["siteAgreements"][0]["versions"][1]["accepted"], True)
