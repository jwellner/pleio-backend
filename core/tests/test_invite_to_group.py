from django.contrib.auth.models import AnonymousUser
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from unittest import mock


class InviteToGroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user1, 'owner')

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()

        super().tearDown()

    @mock.patch('core.resolvers.mutation_invite_to_group.generate_code', return_value='6df8cdad5582833eeab4')
    @mock.patch('core.resolvers.mutation_invite_to_group.schedule_invite_to_group_mail')
    def test_invite_to_group_by_guid_by_group_owner(self, mocked_mail, mocked_generate_code):
        mutation = """
            mutation InviteItem($input: inviteToGroupInput!) {
                inviteToGroup(input: $input) {
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
                "directAdd": False,
                "guid": self.group1.guid,
                "users": [{"guid": self.user2.guid}]
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result['data']

        self.assertEqual(data["inviteToGroup"]["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_invite_to_group.generate_code', return_value='6df8cdad5582833eeab4')
    @mock.patch('core.resolvers.mutation_invite_to_group.schedule_invite_to_group_mail')
    def test_invite_to_group_by_email_by_group_owner(self, mocked_mail, mocked_generate_code):
        mutation = """
            mutation InviteItem($input: inviteToGroupInput!) {
                inviteToGroup(input: $input) {
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
                "directAdd": False,
                "guid": self.group1.guid,
                "users": [{"email": self.user2.email}]
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result['data']

        self.assertEqual(data["inviteToGroup"]["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_mail.call_count, 1)

    def test_direct_add_users_to_group_by_group_owner(self):
        mutation = """
            mutation InviteItem($input: inviteToGroupInput!) {
                inviteToGroup(input: $input) {
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
                "directAdd": True,
                "guid": self.group1.guid,
                "users": [{"guid": self.user2.guid}]
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(mutation, variables)

    def test_direct_add_users_to_group_by_admin(self):
        mutation = """
            mutation InviteItem($input: inviteToGroupInput!) {
                inviteToGroup(input: $input) {
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
                "directAdd": True,
                "guid": self.group1.guid,
                "users": [{"guid": self.user2.guid}]
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["inviteToGroup"]["group"]["guid"], self.group1.guid)
        self.assertEqual(len(self.group1.members.all()), 2)

    @mock.patch('core.resolvers.mutation_invite_to_group.generate_code', return_value='6df8cdad5582833eeab4')
    @mock.patch('core.resolvers.mutation_invite_to_group.schedule_invite_to_group_mail')
    def test_invite_non_site_member_to_group_by_guid_by_group_owner(self, mocked_mail, mocked_generate_code):
        mutation = """
            mutation InviteItem($input: inviteToGroupInput!) {
                inviteToGroup(input: $input) {
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
                "directAdd": False,
                "guid": self.group1.guid,
                "users": [{"email": "test@test.nl"}]
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result['data']

        self.assertEqual(data["inviteToGroup"]["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_mail.call_count, 1)
