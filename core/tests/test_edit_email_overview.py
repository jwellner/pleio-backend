from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory, UserFactory


class EditEmailOverviewTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user1 = UserFactory(email="owner@localhost")
        self.user2 = UserFactory(email="another@localhost")
        self.admin = AdminFactory()

        self.mutation = """
        mutation editEmailOverview($input: editEmailOverviewInput!) {
            editEmailOverview(input: $input) {
                user {
                    guid
                    emailOverview {
                        frequency
                        tags
                        tagCategories {
                            name
                            values
                        }
                    }
                    __typename
                }
                __typename
            }
        }
        """

        self.variables = {
            "input": {
                "guid": self.user1.guid,
                "frequency": "monthly",
                "tags": ["Monday", "Wednesday"],
                "tagCategories": [{"name": "Demo", "values": ["Primary"]}]
            }
        }

    def assertValidResult(self, msg):
        data = self.graphql_client.result["data"]['editEmailOverview']['user']
        self.assertEqual(data["guid"], self.user1.guid, msg=msg)
        self.assertEqual(data["emailOverview"]["frequency"], self.variables['input']['frequency'], msg=msg)
        self.assertEqual(data["emailOverview"]["tags"], self.variables['input']['tags'], msg=msg)
        self.assertEqual(data["emailOverview"]["tagCategories"], self.variables['input']['tagCategories'], msg=msg)

    def test_edit_email_overview_by_authorized_users(self):
        for user, username in [(self.user1, "owner"),
                               (self.admin, "admin")]:
            self.graphql_client.force_login(user)
            self.graphql_client.post(self.mutation, self.variables)
            self.assertValidResult(msg=f"Unexepctedly not stored properly when executed as {username}")

    def test_edit_email_overview_by_non_authorized_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_email_overview_by_anonymous_visitor(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)
