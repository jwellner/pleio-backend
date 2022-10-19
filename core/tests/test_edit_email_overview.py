from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class EditEmailOverviewTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()

    def tearDown(self):
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()
        super().tearDown()

    def test_edit_email_overview_by_owner(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview {
                            frequency
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.user1.guid,
                "frequency": "monthly"
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editEmailOverview"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editEmailOverview"]["user"]["emailOverview"]["frequency"], "monthly")

    def test_edit_email_overview_by_admin(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview {
                            frequency
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.user1.guid,
                "frequency": "monthly"
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editEmailOverview"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editEmailOverview"]["user"]["emailOverview"]["frequency"], "monthly")

    def test_edit_email_overview_by_logged_in_user(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview {
                            frequency
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "frequency": "monthly"
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(mutation, variables)

    def test_edit_email_overview_by_anonymous(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview {
                            frequency
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.user1.guid,
                "frequency": "monthly"
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_edit_email_overview_by_owner_add_tag(self):
        mutation = """
            mutation editEmailOverview($input: editEmailOverviewInput!) {
                editEmailOverview(input: $input) {
                    user {
                        guid
                        emailOverview {
                            frequency
                            tags
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.user1.guid,
                "tags": ['tag_one']
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editEmailOverview"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editEmailOverview"]["user"]["emailOverview"]["tags"][0], 'tag_one')
