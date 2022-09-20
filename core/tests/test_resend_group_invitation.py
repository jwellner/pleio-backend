from django.contrib.auth.models import AnonymousUser
from core.models import Group, GroupInvitation
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from unittest import mock


class ResendGroupInvitationTestCase(PleioTenantTestCase):

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
        self.group1.join(self.user1, 'owner')
        self.invitation = GroupInvitation.objects.create(code="7d97cea90c83722c7262", invited_user=self.user2, group=self.group1)

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user3.delete()
        self.user2.delete()
        self.user1.delete()

        super().tearDown()

    @mock.patch('core.resolvers.mutation_resend_group_invitation.schedule_resend_group_invitation_mail')
    def test_resend_group_invitation_by_group_owner(self, mocked_mail):
        mutation = """
            mutation InvitedList($input: resendGroupInvitationInput!) {
                resendGroupInvitation(input: $input) {
                    group {
                    guid
                    name
                    invited {
                        total
                        edges {
                        id
                        invited
                        timeCreated
                        email
                        user {
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
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "id": self.invitation.id,
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)
        data = result["data"]["resendGroupInvitation"]

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_resend_group_invitation.schedule_resend_group_invitation_mail')
    def test_resend_group_invitation_by_admin(self, mocked_mail):
        mutation = """
            mutation InvitedList($input: resendGroupInvitationInput!) {
                resendGroupInvitation(input: $input) {
                    group {
                    guid
                    name
                    invited {
                        total
                        edges {
                        id
                        invited
                        timeCreated
                        email
                        user {
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
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "id": self.invitation.id,
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)
        data = result["data"]["resendGroupInvitation"]

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertEqual(mocked_mail.call_count, 1)

    @mock.patch('core.resolvers.mutation_resend_group_invitation.schedule_resend_group_invitation_mail')
    def test_resend_group_invitation_by_non_group_member(self, mocked_mail):
        mutation = """
            mutation InvitedList($input: resendGroupInvitationInput!) {
                resendGroupInvitation(input: $input) {
                    group {
                    guid
                    name
                    invited {
                        total
                        edges {
                        id
                        invited
                        timeCreated
                        email
                        user {
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
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "id": self.invitation.id,
            }
        }

        with self.assertGraphQlError("could_not_invite"):
            self.graphql_client.force_login(self.user3)
            self.graphql_client.post(mutation, variables)

    @mock.patch('core.resolvers.mutation_resend_group_invitation.schedule_resend_group_invitation_mail')
    def test_resend_group_invitation_by_anonymous_user(self, mocked_mail):
        mutation = """
            mutation InvitedList($input: resendGroupInvitationInput!) {
                resendGroupInvitation(input: $input) {
                    group {
                    guid
                    name
                    invited {
                        total
                        edges {
                        id
                        invited
                        timeCreated
                        email
                        user {
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
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "id": self.invitation.id,
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)
