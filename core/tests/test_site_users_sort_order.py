from django.utils import timezone

from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestSiteUsersSortOrderTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.authenticatedUser = UserFactory(
            name='user',
            created_at=timezone.now())
        self.admin = AdminFactory(
            name='admin',
            created_at=timezone.now() - timezone.timedelta(days=1))

        self.user1 = UserFactory(
            name='user1',
            created_at=timezone.now() - timezone.timedelta(days=100))
        self.user2 = UserFactory(
            name='user2',
            created_at=timezone.now() - timezone.timedelta(days=50))
        self.user3 = UserFactory(
            name='user3',
            created_at=timezone.now() - timezone.timedelta(days=75))

        self.query = """
        query UsersInOrderOfCreatedAt($field: String, $dir: OrderDirection) {
            siteUsers(orderBy: $field, orderDirection: $dir) {
                edges {
                    name
                    memberSince
                }
            } 
        }
        """

    def test_authenticated_user_has_no_access(self):
        self.graphql_client.force_login(self.authenticatedUser)
        with self.assertGraphQlError('user_not_site_admin'):
            self.graphql_client.post(self.query, {
                'field': 'memberSince',
                'dir': 'asc'
            })

    def test_query_site_users_by_created_at_order(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {
            'field': 'memberSince',
            'dir': 'asc'
        })
        self.assertEqual([u['name'] for u in result['data']['siteUsers']['edges']],
                         ['user1', 'user3', 'user2', 'admin', 'user'])

    def test_query_site_users_by_created_at_order_desc(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {
            'field': 'memberSince',
            'dir': 'desc'
        })
        self.assertEqual([u['name'] for u in result['data']['siteUsers']['edges']],
                         ['user', 'admin', 'user2', 'user3', 'user1'])
