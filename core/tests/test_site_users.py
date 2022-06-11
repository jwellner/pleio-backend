from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory, EditorFactory
from django.utils import dateparse, timezone

from user.models import User


class SiteUsersTestCase(PleioTenantTestCase):

    def setUp(self):
        super(SiteUsersTestCase, self).setUp()

        self.user1 = UserFactory(name="Tt")
        self.user2 = UserFactory(name="Specific_user_name_1",
                                 email='specific@test.nl')
        self.user3 = UserFactory(is_delete_requested=True, name="Zz")
        self.user4 = UserFactory(is_active=False, name='Xx')
        self.user5 = UserFactory()
        self.user5.delete()
        self.admin1 = AdminFactory(name='Yy')
        self.admin2 = AdminFactory(name='Uu')
        self.editor1 = EditorFactory(name='Vv')

        self.user1.profile.last_online = dateparse.parse_datetime("2018-12-10T23:00:00.000Z")
        self.user1.profile.save()
        self.user3.profile.last_online = "2020-12-10T23:00:00.000Z"
        self.user3.profile.save()
        self.user4.profile.last_online = "2020-12-10T23:00:00.000Z"
        self.user4.profile.save()

        self.query = """
            query UsersQuery(
                    $offset: Int,
                    $limit: Int
                    $q: String
                    $role: String
                    $isDeleteRequested: Boolean
                    $isBanned: Boolean
                    $memberSince: DateTime
                    $lastOnlineBefore: String) {
                siteUsers(
                        offset: $offset
                        limit: $limit
                        q: $q
                        role: $role
                        isDeleteRequested: $isDeleteRequested
                        isBanned: $isBanned
                        memberSince: $memberSince
                        lastOnlineBefore: $lastOnlineBefore) {
                    edges {
                        guid
                        name
                        url
                        email
                        lastOnline
                        roles
                        requestDelete
                        memberSince
                    }
                    total
                }
            }
        """

    def tearDown(self):
        self.admin1.delete()
        self.admin2.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.user4.delete()

    def test_site_users_get_all_by_admin(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {})

        data = result["data"]['siteUsers']
        self.assertEqual(data["total"], 6)
        self.assertEqual(data["edges"][0]["name"], self.user2.name)
        self.assertEqual(len(data["edges"]), 6)

    def test_site_users_filter_admins_by_admin(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {"role": "admin"})

        data = result["data"]['siteUsers']
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["edges"]), 2)

    def test_site_users_filter_editors_by_admin(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {"role": "editor"})

        data = result["data"]
        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(len(data["siteUsers"]["edges"]), 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.editor1.guid)
        self.assertEqual(data["siteUsers"]["edges"][0]["roles"], self.editor1.roles)

    def test_site_users_filter_delete_requested_by_admin(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {"isDeleteRequested": True})

        data = result["data"]
        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user3.guid)

    def test_site_users_filter_name_by_admin(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {"q": "c_user_nam"})

        data = result["data"]
        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)

    def test_site_users_filter_email_guid_by_admin(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {"q": "specific@test.nl"})

        data = result["data"]
        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)
        self.assertEqual(data["siteUsers"]["edges"][0]["email"], self.user2.email)

        result = self.graphql_client.post(self.query, {"q": "cific@test.nl"})

        data = result["data"]
        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)
        self.assertEqual(data["siteUsers"]["edges"][0]["email"], self.user2.email)

        result = self.graphql_client.post(self.query, {"q": self.user2.guid})

        data = result["data"]
        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["guid"], self.user2.guid)
        self.assertEqual(data["siteUsers"]["edges"][0]["email"], self.user2.email)

    def test_site_users_by_anonymous(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.query, {})

    def test_site_users_by_user(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(self.query, {})

    def test_site_users_get_all_banned_by_admin(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {"isBanned": True})

        data = result["data"]
        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(len(data["siteUsers"]["edges"]), 1)
        self.assertEqual(data["siteUsers"]["edges"][0]['guid'], self.user4.guid)

    def test_site_users_get_lastonline_before_by_admin(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {"lastOnlineBefore": "2019-12-10T23:00:00.000Z"})

        data = result["data"]
        self.assertEqual(data["siteUsers"]["total"], 1)
        self.assertEqual(data["siteUsers"]["edges"][0]["name"], self.user1.name)
        self.assertEqual(len(data["siteUsers"]["edges"]), 1)

    def test_site_users_result(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {'q': self.user1.name})

        user = result['data']['siteUsers']['edges'][0]

        self.assertEqual(user['guid'], self.user1.guid)
        self.assertEqual(user['name'], self.user1.name)
        self.assertEqual(user['url'], self.user1.url)
        self.assertEqual(user['email'], self.user1.email)
        self.assertDateEqual(user['lastOnline'], str(self.user1.profile.last_online))
        self.assertDateEqual(user['memberSince'], str(self.user1.created_at))

    def test_site_users_members_since(self):
        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, {'memberSince': str(timezone.now())})

        self.assertEqual(result['data']['siteUsers']['total'], 0)

        result = self.graphql_client.post(self.query, {
            'memberSince': str(timezone.now() - timezone.timedelta(days=1))
        })

        self.assertTrue(result['data']['siteUsers']['total'] > 0)
