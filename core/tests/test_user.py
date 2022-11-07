from blog.factories import BlogFactory
from core.tests.helpers import PleioTenantTestCase, ElasticsearchTestCase
from user.factories import UserFactory, AdminFactory


class TestAdminUserTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory(name="User")
        self.admin = AdminFactory(name="Admin")
        self.superadmin = UserFactory(is_superadmin=True, name="Superadmin")

        BlogFactory(owner=self.user)
        BlogFactory(owner=self.admin)
        BlogFactory(owner=self.superadmin)

        self.query = """
            query Entities {
                entities {
                    edges {
                        ... on Blog {
                            owner {
                                name
                                canDelete
                                canBan
                            }
                        }
                    }
                }
            }
        """

    def fetch_users(self):
        result = self.graphql_client.post(self.query, {})
        return {edge['owner']['name']: edge['owner'] for edge in result['data']['entities']['edges']}

    def assertFullControl(self, properties, msg=None):
        self.assertTrue(properties['canDelete'], msg=msg)
        self.assertTrue(properties['canBan'], msg=msg)

    def assertNoControl(self, properties, msg=None):
        self.assertFalse(properties['canDelete'], msg=msg)
        self.assertFalse(properties['canBan'], msg=msg)

    def test_anonymous_visitor_on_full_control_about_users(self):
        result = self.fetch_users()

        self.assertNoControl(result['User'], msg="Anonymous at User")
        self.assertNoControl(result['Admin'], msg="Anonymous at Admin")
        self.assertNoControl(result['Superadmin'], msg="Anonymous at Superadmin")

    def test_user_on_full_control_about_users(self):
        BlogFactory(owner=UserFactory(name="User2"))
        self.graphql_client.force_login(self.user)

        result = self.fetch_users()

        self.assertNoControl(result['User'], msg="User at User")
        self.assertNoControl(result['User2'], msg="User at User2")
        self.assertNoControl(result['Admin'], msg="User at Admin")
        self.assertNoControl(result['Superadmin'], msg="User at Superadmin")

    def test_admin_on_full_control_about_users(self):
        BlogFactory(owner=AdminFactory(name="Admin2"))
        self.graphql_client.force_login(self.admin)

        result = self.fetch_users()

        self.assertFullControl(result['User'], msg="Admin at User")
        self.assertNoControl(result['Admin'], msg="Admin at Admin")
        self.assertFullControl(result['Admin2'], msg="Admin at Admin2")
        self.assertNoControl(result['Superadmin'], msg="Admin at Superadmin")

    def test_superadmin_on_full_control_about_users(self):
        BlogFactory(owner=UserFactory(is_superadmin=True, name="Superadmin2"))
        self.graphql_client.force_login(self.superadmin)

        result = self.fetch_users()

        self.assertFullControl(result['User'], msg="Superadmin at User")
        self.assertFullControl(result['Admin'], msg="Superadmin at Admin")
        self.assertNoControl(result['Superadmin'], msg="Superadmin at Superadmin")
        self.assertFullControl(result['Superadmin2'], msg="Superadmin at Superadmin2")


class TestUserTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user1 = UserFactory(name="Aa")
        self.user2 = AdminFactory(name="Bb")

        self.query = """
            query UserList($query: String!, $offset: Int, $limit: Int) {
                users(q: $query, offset: $offset, limit: $limit) {
                    total
                    edges {
                        guid
                        canDelete
                        canBan
                    }
                }
            }
        """

    def test_user_query_not_logged_in(self):
        variables = {
            "query": "",
            "offset": 0,
            "limit": 20
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.query, variables)

    def test_users_query(self):
        variables = {
            "query": "Aa",
            "offset": 0,
            "limit": 20
        }

        ElasticsearchTestCase.initialize_index()

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["users"]["edges"][0]["guid"], self.user1.guid)

    def test_users_no_query(self):
        variables = {
            "query": "",
            "offset": 0,
            "limit": 20
        }

        ElasticsearchTestCase.initialize_index()

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["users"]["total"], 2)

    def test_dont_show_superadmins_in_public_userpage(self):
        superadmin1 = UserFactory(is_superadmin=True, name="Cc")
        variables = {
            "query": superadmin1.name,
            "offset": 0,
            "limit": 20
        }

        ElasticsearchTestCase.initialize_index()

        self.graphql_client.force_login(superadmin1)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(0, result['data']['users']['total'])
        self.assertEqual(0, len(result['data']['users']['edges']))
