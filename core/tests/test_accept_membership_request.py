from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from mixer.backend.django import mixer
from unittest import mock


class AcceptMembershipRequestTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.user3 = UserFactory()
        self.admin = AdminFactory()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user2, 'pending')

        self.mutation = """
            mutation MembershipRequestsList($input: acceptMembershipRequestInput!) {
                acceptMembershipRequest(input: $input) {
                    group {
                        guid
                        name
                        membershipRequests {
                            total
                            edges {
                                guid
                                username
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
            }
        """

        self.variables = {
            "input": {
                "userGuid": self.user2.guid,
                "groupGuid": self.group1.guid
            }
        }

    def test_accept_group_access_request_by_group_owner(self):
        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.mutation, self.variables)

        self.assertEqual(result["data"]["acceptMembershipRequest"]["group"]["guid"], self.group1.guid)

    def test_accept_group_access_request_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)

        self.assertEqual(result["data"]["acceptMembershipRequest"]["group"]["guid"], self.group1.guid)

    def test_accept_group_access_request_by_other_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user3)
            self.graphql_client.post(self.mutation, self.variables)

    def test_accept_group_access_request_by_anonymous(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation, self.variables)
