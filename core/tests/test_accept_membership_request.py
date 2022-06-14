from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from mixer.backend.django import mixer
from unittest import mock


class AcceptMembershipRequestTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AcceptMembershipRequestTestCase, self).setUp()

        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.user3 = UserFactory()
        self.admin = AdminFactory()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user2, 'pending')

    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi.delay')
    def test_accept_group_access_request_by_group_owner(self, mocked_send_mail_multi):
        mutation = """
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

        variables = {
            "input": {
                "userGuid": self.user2.guid,
                "groupGuid": self.group1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        self.assertEqual(result["data"]["acceptMembershipRequest"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once()

    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi.delay')
    def test_accept_group_access_request_by_admin(self, mocked_send_mail_multi):
        mutation = """
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

        variables = {
            "input": {
                "userGuid": self.user2.guid,
                "groupGuid": self.group1.guid
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        self.assertEqual(result["data"]["acceptMembershipRequest"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once()

    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_accept_group_access_request_by_other_user(self, mocked_send_mail_multi):
        mutation = """
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

        variables = {
            "input": {
                "userGuid": self.user2.guid,
                "groupGuid": self.group1.guid
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user3)
            self.graphql_client.post(mutation, variables)

        assert not mocked_send_mail_multi.called

    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_accept_group_access_request_by_anonymous(self, mocked_send_mail_multi):
        mutation = """
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

        variables = {
            "input": {
                "userGuid": self.user2.guid,
                "groupGuid": self.group1.guid
            }
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(mutation, variables)

        assert not mocked_send_mail_multi.called
