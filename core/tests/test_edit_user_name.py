from django.db import connection

from core.tests.helpers import PleioTenantTestCase
from mixer.backend.django import mixer
from user.models import User
from django.core.cache import cache


class EditUserNameTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.user_other = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        cache.set("%s%s" % (connection.schema_name, 'EDIT_USER_NAME_ENABLED'), True)

    def tearDown(self):
        self.user.delete()
        self.user_other.delete()
        self.admin.delete()
        super().tearDown()

    def test_edit_user_name_by_admin(self):
        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editUserName"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editUserName"]["user"]["name"], "Jantje")

    def test_edit_user_name_by_anonymous(self):
        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_edit_user_name_by_self(self):
        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editUserName"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editUserName"]["user"]["name"], "Jantje")

    def test_edit_user_name_by_self_disabled(self):
        cache.set("%s%s" % (connection.schema_name, 'EDIT_USER_NAME_ENABLED'), False)

        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_edit_user_name_by_other_user(self):
        mutation = """
            mutation editUserName($input: editUserNameInput!) {
                editUserName(input: $input) {
                    user {
                        guid
                        name
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user.guid,
                "name": "Jantje"
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user_other)
            self.graphql_client.post(mutation, variables)
