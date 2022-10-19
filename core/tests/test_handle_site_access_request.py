from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.models import SiteAccessRequest
from core.constances import USER_ROLES
from mixer.backend.django import mixer
from unittest import mock


class HandleSiteAccessRequestTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.request1 = mixer.blend(SiteAccessRequest, email='test1@pleio.nl', claims={'email': 'test1@pleio.nl', 'name': 'Test 123', 'sub': 1})

        self.mutation = """
            mutation SiteAccessRequest($input: handleSiteAccessRequestInput!) {
                handleSiteAccessRequest(input: $input) {
                    success
                }
            }
        """

    def tearDown(self):
        self.admin.delete()
        self.user.delete()
        super().tearDown()

    @mock.patch('core.resolvers.mutation_handle_site_access_request.schedule_site_access_request_accepted_mail')
    def test_handle_access_request_by_admin(self, mocked_mail):
        variables = {
            "input": {
                "email": "test1@pleio.nl",
                "accept": True
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["handleSiteAccessRequest"]["success"], True)
        self.assertTrue(SiteAccessRequest.objects.filter(email=self.request1.email, accepted=True).exists())
        self.assertFalse(User.objects.filter(email=self.request1.email).exists())
        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_handle_site_access_request.schedule_site_access_request_denied_mail')
    def test_handle_access_request_deny_by_admin(self, mocked_mail):
        variables = {
            "input": {
                "email": "test1@pleio.nl",
                "accept": False
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["handleSiteAccessRequest"]["success"], True)
        self.assertFalse(User.objects.filter(email=self.request1.email).exists())
        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_handle_site_access_request.schedule_site_access_request_denied_mail')
    def test_handle_access_request_deny_silent_by_admin(self, mocked_mail):
        variables = {
            "input": {
                "email": "test1@pleio.nl",
                "accept": False,
                "silent": True
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["handleSiteAccessRequest"]["success"], True)
        self.assertFalse(User.objects.filter(email=self.request1.email).exists())
        self.assertFalse(mocked_mail.called)

    def test_handle_access_request_by_user(self):
        variables = {
            "input": {
                "email": "test1@pleio.nl",
                "accept": True
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, variables)

    def test_handle_access_request_by_anonymous(self):
        variables = {
            "input": {
                "email": "test1@pleio.nl",
                "accept": True
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, variables)
