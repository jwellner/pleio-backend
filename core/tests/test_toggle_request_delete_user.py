
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from user.models import User


class ToggleRequestDeleteUserTestCase(PleioTenantTestCase):

    def setUp(self):
        super(ToggleRequestDeleteUserTestCase, self).setUp()

        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])

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

    @mock.patch('core.resolvers.mutation_toggle_request_delete_user.send_mail_multi.delay')
    def test_call_send_email(self, mocked_send_mail_multi):
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        assert mocked_send_mail_multi.called

    @mock.patch('core.resolvers.mutation_toggle_request_delete_user.send_mail_multi.delay')
    def test_call_send_email(self, mocked_send_mail_multi):

        self.user1.is_delete_requested = True
        
        variables = {
            "input": {
                "guid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        assert mocked_send_mail_multi.called
