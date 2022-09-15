from backend2.schema import schema
from ariadne import graphql_sync
from django.http import HttpRequest
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from user.models import User
from mixer.backend.django import mixer
from unittest import mock


class ToggleUserRoleTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = UserFactory()
        self.user2 = AdminFactory()
        self.admin = AdminFactory()

        self.mutation = """
            mutation toggleUserRole($input: toggleUserRoleInput!) {
                toggleUserRole(input: $input) {
                    success
                }
            }
        """
        self.variables = {
            "input": {
                "guid": self.user1.guid,
                "role": "admin"
            }
        }

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        self.admin.delete()
        super().tearDown()

    def test_toggle_user_role_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_toggle_user_role_by_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(self.mutation, self.variables)

    @mock.patch('core.resolvers.mutation_toggle_user_role.schedule_assign_admin_for_admin_mail')
    @mock.patch('core.resolvers.mutation_toggle_user_role.schedule_assign_admin_for_user_mail')
    def test_toggle_user_role_switch_on(self, mail_for_user, mail_for_admin):
        self.graphql_client.force_login(self.admin)
        self.graphql_client.post(self.mutation, self.variables)

        self.assertTrue(mail_for_user.called)
        self.assertTrue(mail_for_admin.called)

    @mock.patch('core.resolvers.mutation_toggle_user_role.schedule_revoke_admin_for_admin_mail')
    @mock.patch('core.resolvers.mutation_toggle_user_role.schedule_revoke_admin_for_user_mail')
    def test_toggle_user_role_switch_off(self, mail_for_user, mail_for_admin):
        self.variables['input']['guid'] = self.user2.guid

        self.graphql_client.force_login(self.admin)
        self.graphql_client.post(self.mutation, self.variables)

        self.assertTrue(mail_for_user.called)
        self.assertTrue(mail_for_admin.called)


