from django_tenants.test.cases import FastTenantTestCase
from django.contrib.auth.models import AnonymousUser
from user.models import User
from core.models import SiteAccessRequest
from core.constances import USER_ROLES
from mixer.backend.django import mixer
from backend2.schema import schema
from ariadne import graphql_sync
from django.http import HttpRequest
from unittest import mock
from django.test import override_settings


class HandleDeleteAccountRequestTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
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
        self.admin.delete()
        self.user.delete()

    @mock.patch('core.resolvers.mutation_handle_delete_account_request.send_mail_multi.delay')
    def test_handle_delete_account_request_by_admin(self, mocked_send_mail_multi):

        variables = {
            "input": {
                    "guid": self.delete_user.guid,
                    "accept": True
                }
            }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["handleDeleteAccountRequest"]["success"], True)

        self.delete_user.refresh_from_db()

        self.assertEqual(self.delete_user.name, "Verwijderde gebruiker")
        self.assertEqual(self.delete_user.is_delete_requested, False)
        self.assertEqual(self.delete_user.is_active, False)

        mocked_send_mail_multi.assert_called_once()

    @mock.patch('core.resolvers.mutation_handle_delete_account_request.send_mail_multi.delay')
    def test_handle_delete_account_request_deny_by_admin(self, mocked_send_mail_multi):

        variables = {
            "input": {
                    "guid": self.delete_user.guid,
                    "accept": False
                }
            }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["handleDeleteAccountRequest"]["success"], True)

        self.delete_user.refresh_from_db()

        self.assertEqual(self.delete_user.is_delete_requested, False)
        self.assertEqual(self.delete_user.is_active, True)
        
        mocked_send_mail_multi.assert_not_called()

    def test_handle_delete_account_request_by_user(self):

        variables = {
            "input": {
                    "guid": self.delete_user.guid,
                    "accept": True
                }
            }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]


        self.assertEqual(errors[0]["message"], "user_not_site_admin")


    def test_handle_delete_account_request_by_anonymous(self):

        variables = {
            "input": {
                    "guid": self.delete_user.guid,
                    "accept": True
                }
            }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": self.mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
