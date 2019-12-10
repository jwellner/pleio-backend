from django.conf import settings
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.utils.translation import ugettext_lazy
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, GroupInvitation, User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock


class AcceptGroupInvitationTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.group1 = mixer.blend(Group, owner=self.user1)
        GroupInvitation.objects.create(code="7d97cea90c83722c7262", invited_user=self.user2, group=self.group1)


    def tearDown(self):
        self.group1.delete()
        self.user2.delete()
        self.user1.delete()


    def test_accept_group_inivitation(self):
        mutation = """
            mutation Invitations($input: acceptGroupInvitationInput!) {
                acceptGroupInvitation(input: $input) {
                    group {
                    guid
                    ... on Group {
                        name
                        plugins
                        description
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

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])
        data = result[1]["data"]

        self.assertEqual(data["acceptGroupInvitation"]["group"]["guid"], self.group1.guid)


    def test_accept_group_inivitation_twice(self):
        mutation = """
            mutation Invitations($input: acceptGroupInvitationInput!) {
                acceptGroupInvitation(input: $input) {
                    group {
                    guid
                    ... on Group {
                        name
                        plugins
                        description
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

        request = HttpRequest()
        request.user = self.user2

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        # Call second time
        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "invalid_code")
