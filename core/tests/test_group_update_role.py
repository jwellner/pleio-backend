from core.factories import GroupFactory
from core.models import GroupMembership
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from unittest import mock


class ChangeGroupRoleTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory(email='user1@example.com')
        self.user2 = UserFactory(email='user2@example.com')
        self.user3 = UserFactory(email='user3@example.com')
        self.user4 = UserFactory(email='user4@example.com')
        self.admin = AdminFactory(email='admin@example.com')
        self.group1 = GroupFactory(name="Group1", owner=self.user1)
        self.group1.join(self.user2, 'member')
        self.group1.join(self.user4, 'admin')

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user4.delete()
        self.user3.delete()
        self.user2.delete()
        self.user1.delete()

        super().tearDown()

    @mock.patch('core.resolvers.mutation_change_group_role.schedule_change_group_ownership_mail')
    def test_change_group_role_to_owner_by_group_owner(self, mocked_send_mail):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "owner"
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result["data"]["changeGroupRole"]

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertEqual(self.group1.members.get(user=self.user2).type, 'owner')
        self.assertEqual(self.group1.members.get(user=self.user1).type, 'admin')

    @mock.patch('core.resolvers.mutation_change_group_role.schedule_change_group_ownership_mail')
    def test_change_group_role_to_member_by_group_owner(self, mocked_mail):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user4.guid,
                "role": "member"
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result["data"]["changeGroupRole"]

        self.assertFalse(mocked_mail.called)
        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(self.group1.members.get(user=self.user4).type, 'member')

    @mock.patch('core.resolvers.mutation_change_group_role.schedule_change_group_ownership_mail')
    def test_change_group_role_to_removed_by_group_owner(self, mocked_mail):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    members {
                        total
                        edges {
                            role
                        }
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user4.guid,
                "role": "removed"
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result["data"]["changeGroupRole"]

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertFalse(mocked_mail.called)
        self.assertFalse(self.group1.members.filter(user=self.user4).exists())

    def test_change_group_role_to_admin_by_group_owner(self):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    members {
                        edges {
                            role
                        }
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "admin"
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result["data"]["changeGroupRole"]

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(self.group1.members.get(user=self.user2).type, 'admin')
        self.assertEqual(self.group1.members.get(user=self.user1).type, 'owner')

    @mock.patch('core.resolvers.mutation_change_group_role.schedule_change_group_ownership_mail')
    def test_change_group_role_to_owner_by_admin(self, mocked_send_mail):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "owner"
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)
        data = result["data"]["changeGroupRole"]

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertEqual(self.group1.members.get(user=self.user2).type, 'owner')
        self.assertEqual(self.group1.members.get(user=self.user1).type, 'admin')

    @mock.patch('core.resolvers.mutation_change_group_role.schedule_change_group_ownership_mail')
    def test_change_group_role_to_owner_by_other_user(self, mocked_mail):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "owner"
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user3)
            self.graphql_client.post(mutation, variables)

        self.assertFalse(mocked_mail.called)
        self.assertEqual(self.group1.members.get(user=self.user2).type, 'member')

    @mock.patch('core.resolvers.mutation_change_group_role.schedule_change_group_ownership_mail')
    def test_change_group_role_to_owner_by_anonymous(self, mocked_mail):
        mutation = """
            mutation MemberItem($input: changeGroupRoleInput!) {
                changeGroupRole(input: $input) {
                    group {
                    ... on Group {
                        guid
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuid": self.user2.guid,
                "role": "owner"
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

        self.assertFalse(mocked_mail.called)
        self.assertEqual(self.group1.members.get(user=self.user2).type, 'member')
