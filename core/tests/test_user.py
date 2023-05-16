from mixer.backend.django import mixer

from blog.factories import BlogFactory
from core.models import ProfileField, ProfileSet, UserProfileField
from core.tests.helpers import ElasticsearchTestCase, PleioTenantTestCase
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
                                banReason
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


class TestUserTestCase(ElasticsearchTestCase):
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

        self.initialize_index()

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["users"]["edges"][0]["guid"], self.user1.guid)

    def test_users_no_query(self):
        variables = {
            "query": "",
            "offset": 0,
            "limit": 20
        }

        self.initialize_index()

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

        self.initialize_index()

        self.graphql_client.force_login(superadmin1)
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(0, result['data']['users']['total'])
        self.assertEqual(0, len(result['data']['users']['edges']))


class TestUserProfileSetTestCase(ElasticsearchTestCase):
    def setUp(self):
        super().setUp()

        self.manager = UserFactory()
        self.similar_user = UserFactory()
        self.other_user = UserFactory()

        # Will not get the profile field at all.
        self.invalid_user = UserFactory()

        self.field = mixer.blend(ProfileField,
                                 key="demo_field")
        self.profile_set = ProfileSet.objects.create(
            field=self.field,
            name="Demo profile set"
        )
        self.profile_set.users.add(self.manager)
        self.profile_set.users.add(self.invalid_user)

        UserProfileField.objects.create(
            user_profile=self.manager.profile,
            profile_field=self.field,
            value="similar",
        )
        UserProfileField.objects.create(
            user_profile=self.similar_user.profile,
            profile_field=self.field,
            value="similar"
        )
        UserProfileField.objects.create(
            user_profile=self.other_user.profile,
            profile_field=self.field,
            value="other"
        )

        self.query = """
            query UserList($query: String!, $guid: String) {
                users(q: $query, profileSetGuid: $guid) {
                    total
                    edges {
                        guid
                        email
                    }
                }
            }
        """

        self.variables = {
            'query': '',
            'guid': self.profile_set.guid,
        }

    def tearDown(self):
        super().tearDown()

    def test_similar_users_as_manager(self):
        self.initialize_index()
        self.graphql_client.force_login(self.manager)
        result = self.graphql_client.post(self.query, self.variables)

        user_guids = [e['guid'] for e in result['data']['users']['edges']]
        self.assertEqual(2, len(user_guids))
        self.assertIn(self.manager.guid, user_guids)
        self.assertIn(self.similar_user.guid, user_guids)

    def test_similar_users_as_not_a_manager(self):
        self.initialize_index()
        with self.assertGraphQlError("not_authorized"):
            self.graphql_client.force_login(self.similar_user)
            self.graphql_client.post(self.query, self.variables)

    def test_similar_users_as_invalid_user(self):
        self.initialize_index()
        with self.assertGraphQlError("missing_required_field:demo_field"):
            self.graphql_client.force_login(self.invalid_user)
            self.graphql_client.post(self.query, self.variables)


class TestBanReasonTestCase(PleioTenantTestCase):
    BAN_REASON = "Just for testing"

    def setUp(self):
        super().setUp()
        self.admin = AdminFactory(name='admin', email='admin@localhost')
        self.banned = UserFactory(name='banned', email='banned@localhost',
                                  is_active=False,
                                  ban_reason=self.BAN_REASON)
        self.viewer = UserFactory(name='viewer', email='viewer@localhost')
        self.blog = BlogFactory(owner=self.banned)

        self.query = """
        query GetEntity ($guid: String) {
            entity(guid: $guid) {
                ... on Blog {
                    owner {
                        banReason
                    }
                }
            }
        }
        """
        self.variables = {
            "guid": self.blog.guid,
        }

    def tearDown(self):
        super().tearDown()

    def test_user_info_as_user(self):
        self.graphql_client.force_login(self.viewer)
        result = self.graphql_client.post(self.query, self.variables)
        self.assertIsNone(result['data']['entity']['owner']['banReason'])

    def test_user_info_as_administrator(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, self.variables)
        self.assertEqual(result['data']['entity']['owner']['banReason'], self.BAN_REASON)
