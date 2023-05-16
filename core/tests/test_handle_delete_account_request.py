from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import USER_ROLES
from mixer.backend.django import mixer
from unittest import mock


class HandleDeleteAccountRequestTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.delete_user = mixer.blend(User, is_delete_requested=True)

        self.mutation = """
            mutation handleDeleteAccountRequest($input: handleDeleteAccountRequestInput!) {
                handleDeleteAccountRequest(input: $input) {
                    success
                }
            }
        """

    def tearDown(self):
        super().tearDown()

    @mock.patch('core.resolvers.mutation_handle_delete_account_request.schedule_user_delete_complete_mail')
    def test_handle_delete_account_request_by_admin(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.delete_user.guid,
                "accept": True
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["handleDeleteAccountRequest"]["success"], True)

        self.delete_user.refresh_from_db()
        self.assertEqual(self.delete_user.name, "Verwijderde gebruiker")
        self.assertEqual(self.delete_user.is_delete_requested, False)
        self.assertEqual(self.delete_user.is_active, False)
        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_handle_delete_account_request.schedule_user_delete_complete_mail')
    def test_handle_delete_account_request_deny_by_admin(self, mocked_mail):
        variables = {
            "input": {
                "guid": self.delete_user.guid,
                "accept": False
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["handleDeleteAccountRequest"]["success"], True)

        self.delete_user.refresh_from_db()
        self.assertEqual(self.delete_user.is_delete_requested, False)
        self.assertEqual(self.delete_user.is_active, True)
        self.assertFalse(mocked_mail.called)

    def test_handle_delete_account_request_by_user(self):
        variables = {
            "input": {
                "guid": self.delete_user.guid,
                "accept": True
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, variables)

    def test_handle_delete_account_request_by_anonymous(self):
        variables = {
            "input": {
                "guid": self.delete_user.guid,
                "accept": True
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, variables)
