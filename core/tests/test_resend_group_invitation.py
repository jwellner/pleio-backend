from django.conf import settings
from django.db import connection
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, GroupInvitation
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class ResendGroupInvitationTestCase(FastTenantTestCase):

    def setUp(self):
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

    @mock.patch('core.resolvers.mutation_resend_group_invitation.send_mail_multi.delay')
    def test_resend_group_invitation_by_group_owner(self, mocked_send_mail_multi):
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

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["resendGroupInvitation"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once()

    @mock.patch('core.resolvers.mutation_resend_group_invitation.send_mail_multi.delay')
    def test_resend_group_invitation_by_admin(self, mocked_send_mail_multi):
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

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["resendGroupInvitation"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once()

    @mock.patch('core.resolvers.mutation_resend_group_invitation.send_mail_multi.delay')
    def test_resend_group_invitation_by_non_group_member(self, mocked_send_mail_multi):
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

        request = HttpRequest()
        request.user = self.user3

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_invite")

    @mock.patch('core.resolvers.mutation_resend_group_invitation.send_mail_multi.delay')
    def test_resend_group_invitation_by_anonymous_user(self, mocked_send_mail_multi):
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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")
