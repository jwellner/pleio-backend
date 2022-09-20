from django.contrib.auth.models import AnonymousUser
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from unittest import mock


class RejectMembershipRequestTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user2, 'pending')

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user3.delete()
        self.user2.delete()
        self.user1.delete()

        super().tearDown()

    @mock.patch('core.resolvers.mutation_reject_membership_request.schedule_reject_membership_mail')
    def test_reject_group_access_request_by_group_owner(self, mocked_mail):
        mutation = """
            mutation MembershipRequestsList($input: rejectMembershipRequestInput!) {
                rejectMembershipRequest(input: $input) {
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
        data = result['data']['rejectMembershipRequest']

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_reject_membership_request.schedule_reject_membership_mail')
    def test_reject_group_access_request_by_admin(self, mocked_mail):
        mutation = """
            mutation MembershipRequestsList($input: rejectMembershipRequestInput!) {
                rejectMembershipRequest(input: $input) {
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
        data = result['data']['rejectMembershipRequest']

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_reject_membership_request.schedule_reject_membership_mail')
    def test_reject_group_access_request_by_other_user(self, mocked_mail):
        mutation = """
            mutation MembershipRequestsList($input: rejectMembershipRequestInput!) {
                rejectMembershipRequest(input: $input) {
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

        self.assertFalse(mocked_mail.called)

    @mock.patch('core.resolvers.mutation_reject_membership_request.schedule_reject_membership_mail')
    def test_reject_group_access_request_by_anonymous(self, mocked_mail):
        mutation = """
            mutation MembershipRequestsList($input: rejectMembershipRequestInput!) {
                rejectMembershipRequest(input: $input) {
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

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

        self.assertFalse(mocked_mail.called)
