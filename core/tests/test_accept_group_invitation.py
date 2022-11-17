from core.models import Group, GroupInvitation
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from mixer.backend.django import mixer


class AcceptGroupInvitationTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.user3 = UserFactory()
        self.group1 = mixer.blend(Group, owner=self.user1)
        GroupInvitation.objects.create(code="7d97cea90c83722c7262", invited_user=self.user2, group=self.group1)
        self.group1.join(self.user3, 'member')

    def test_accept_group_inivitation(self):
        mutation = """
            mutation Invitations($input: acceptGroupInvitationInput!) {
                acceptGroupInvitation(input: $input) {
                    group {
                    guid
                    ... on Group {
                        name
                        plugins
                        icon
                        isClosed
                        url
                        canEdit
                        membership
                        members(limit: 1) {
                        total
                        edges {
                            role
                            email
                            user {
                                guid
                                username
                                url
                                name
                                icon
                                __typename
                            }
                            __typename
                        }
                        __typename
                        }
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
                "code": "7d97cea90c83722c7262"
            }
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["acceptGroupInvitation"]["group"]["guid"], self.group1.guid)
        self.assertEqual(len(data["acceptGroupInvitation"]["group"]["members"]["edges"]), 1)
        self.assertEqual(data["acceptGroupInvitation"]["group"]["members"]["total"], 2)

    def test_accept_group_inivitation_twice(self):
        mutation = """
            mutation Invitations($input: acceptGroupInvitationInput!) {
                acceptGroupInvitation(input: $input) {
                    group {
                    guid
                    ... on Group {
                        name
                        plugins
                        icon
                        isClosed
                        url
                        canEdit
                        membership
                        members(limit: 5) {
                        total
                        edges {
                            role
                            email
                            user {
                                guid
                                username
                                url
                                name
                                icon
                                __typename
                            }
                            __typename
                        }
                        __typename
                        }
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
                "code": "7d97cea90c83722c7262"
            }
        }

        self.graphql_client.force_login(self.user2)
        self.graphql_client.post(mutation, variables)

        with self.assertGraphQlError("invalid_code"):
            self.graphql_client.post(mutation, variables)
