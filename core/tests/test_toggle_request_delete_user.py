from unittest import mock

from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class ToggleRequestDeleteUserTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory(is_delete_requested=False)
        self.admin = AdminFactory()

        self.mutation = """
            mutation toggleRequestDeleteUser($input: toggleRequestDeleteUserInput!) {
                toggleRequestDeleteUser(input: $input) {
                    viewer {
                        guid
                    }
                }
            }
        """

    def tearDown(self):
        self.user1.delete()
        self.admin.delete()
        super().tearDown()

    def test_toggle_request_delete_not_logged_in(self):
        
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_request_delete_could_not_save(self):

        variables = {
            "input": {
                "guid": self.admin.guid
            }
        }

        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_request_delete_could_not_find(self):
        variables = {
            "input": {
                "guid": "43ee295a-5950-4330-8f0e-372f9f4caddf"
            }
        }

        with self.assertGraphQlError('could_not_find'):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(self.mutation, variables)

    def test_toggle_request_delete_user(self):
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.mutation, variables)
        
        data = result["data"]

        self.assertEqual(data["toggleRequestDeleteUser"]["viewer"]["guid"], self.user1.guid)

    @mock.patch('core.resolvers.mutation_toggle_request_delete_user.schedule_user_request_delete_for_user_mail')
    @mock.patch('core.resolvers.mutation_toggle_request_delete_user.schedule_user_request_delete_for_admin_mail')
    def test_call_send_email_on_toggle_on(self, mail_for_admin, mail_for_user):
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)
        self.user1.refresh_from_db()

        self.assertTrue(self.user1.is_delete_requested)
        self.assertTrue(mail_for_user.called)
        self.assertTrue(mail_for_admin.called)

    # Hier moet nog iets gebeuren
    @mock.patch('core.resolvers.mutation_toggle_request_delete_user.schedule_user_cancel_delete_for_user_mail')
    @mock.patch('core.resolvers.mutation_toggle_request_delete_user.schedule_user_cancel_delete_for_admin_mail')
    def test_call_send_email_on_untoggle(self, mail_for_admin, mail_for_user):

        self.user1.is_delete_requested = True
        self.user1.save()
        
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)
        self.user1.refresh_from_db()

        self.assertFalse(self.user1.is_delete_requested)
        self.assertTrue(mail_for_user.called)
        self.assertTrue(mail_for_admin.called)
