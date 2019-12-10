from django.conf import settings
from django.db import connection
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.utils.translation import ugettext_lazy
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class InviteToGroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        self.group1 = mixer.blend(Group, owner=self.user1)
        self.group1.join(self.user1, 'owner')

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()


    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_invite_to_group.generate_code', return_value='6df8cdad5582833eeab4')
    @mock.patch('core.resolvers.mutation_invite_to_group.send_mail_multi')
    def test_invite_to_group_by_group_owner(self, mocked_send_mail_multi, mocked_generate_code):
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
                "addAllUsers": False,
                "directAdd": False,
                "guid": self.group1.guid,
                "users": [{"guid": self.user2.guid}]
                }
            }

        request = HttpRequest()
        request.user = self.user1
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        link = "https://test.test/groups/invitations/?invitecode=6df8cdad5582833eeab4"
        subject = ugettext_lazy("Invitation to become a member of the %s group" % self.group1.name)

        self.assertEqual(data["inviteToGroup"]["group"]["guid"], self.group1.guid)
        mocked_send_mail_multi.assert_called_once_with(subject, 'email/invite_to_group.html', {'link': link, 'group_name': self.group1.name,
                                                       'user_name': self.user1.name}, [self.user2.email])

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_invite_to_group.send_mail_multi')
    def test_add_all_users_to_group_by_admin(self, mocked_send_mail_multi):
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
                "addAllUsers": True,
                "directAdd": False,
                "guid": self.group1.guid,
                "users": [{"guid": self.user2.guid}]
                }
            }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["inviteToGroup"]["group"]["guid"], self.group1.guid)
        self.assertEqual(len(self.group1.members.all()), 3)
        assert not mocked_send_mail_multi.called

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_add_all_users_to_group_by_group_owner(self, mocked_send_mail_multi):
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
                "addAllUsers": True,
                "directAdd": False,
                "guid": self.group1.guid,
                "users": [{"guid": self.user2.guid}]
                }
            }

        request = HttpRequest()
        request.user = self.user1
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")
        assert not mocked_send_mail_multi.called

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_direct_add_users_to_group_by_group_owner(self, mocked_send_mail_multi):
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
                "addAllUsers": False,
                "directAdd": True,
                "guid": self.group1.guid,
                "users": [{"guid": self.user2.guid}]
                }
            }

        request = HttpRequest()
        request.user = self.user1
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")
        assert not mocked_send_mail_multi.called

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('core.resolvers.mutation_accept_membership_request.send_mail_multi')
    def test_direct_add_users_to_group_by_admin(self, mocked_send_mail_multi):
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
                "addAllUsers": False,
                "directAdd": True,
                "guid": self.group1.guid,
                "users": [{"guid": self.user2.guid}]
                }
            }

        request = HttpRequest()
        request.user = self.admin
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["inviteToGroup"]["group"]["guid"], self.group1.guid)
        self.assertEqual(len(self.group1.members.all()), 2)
        assert not mocked_send_mail_multi.called
