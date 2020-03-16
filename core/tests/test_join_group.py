from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError

class JoinGroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.group_auto = mixer.blend(Group, owner=self.user1, is_membership_on_request=False, is_auto_membership_enabled=True)

        self.user2 = mixer.blend(User) # auto joined to group_auto
        self.user3 = mixer.blend(User) # auto joined to group_auto
        self.group = mixer.blend(Group, owner=self.user1, is_membership_on_request=False)
        self.group_on_request = mixer.blend(Group, owner=self.user1, is_membership_on_request=True)

    def tearDown(self):
        self.group.delete()
        self.group_on_request.delete()
        self.group_auto.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

    def test_join_group_anon(self):
        mutation = """
            mutation ($group: joinGroupInput!) {
                joinGroup(input: $group) {
                    group {
                        members {
                            total
                        }
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_join_group(self):
        mutation = """
            mutation ($group: joinGroupInput!) {
                joinGroup(input: $group) {
                    group {
                        members {
                            total
                            edges {
                                user {
                                    guid
                                }
                            }
                        }
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid
            }
        }

        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["joinGroup"]["group"]["members"]["total"], 1)
        self.assertEqual(data["joinGroup"]["group"]["members"]["edges"][0]["user"]["guid"], self.user1.guid)

        request.user = self.user2
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["joinGroup"]["group"]["members"]["total"], 2)
        self.assertEqual(data["joinGroup"]["group"]["members"]["edges"][0]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["joinGroup"]["group"]["members"]["edges"][1]["user"]["guid"], self.user2.guid)

        self.assertEqual(self.user1.memberships.filter(group=self.group, type="member").count(), 1)
        self.assertEqual(self.user2.memberships.filter(group=self.group, type="member").count(), 1)

    def test_join_group_on_request(self):
        mutation = """
            mutation ($group: joinGroupInput!) {
                joinGroup(input: $group) {
                    group {
                        members {
                            total
                            edges {
                                user {
                                    guid
                                }
                            }
                        }
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group_on_request.guid
            }
        }

        request = HttpRequest()
        request.user = self.user2
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["joinGroup"]["group"]["members"]["total"], 0)

        request.user = self.user3
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["joinGroup"]["group"]["members"]["total"], 0)
        self.assertEqual(self.user2.memberships.filter(group=self.group_on_request, type="pending").count(), 1)
        self.assertEqual(self.user3.memberships.filter(group=self.group_on_request, type="pending").count(), 1)


    def test_auto_membership(self):
        """
        New users should be added automatically on create when auto_membership is enabled
        """

        query = """
            query GroupMembers($guid: String!) {
                entity(guid: $guid) {
                    guid
                    ... on Group {
                        members {
                            total
                            edges {
                                user {
                                    guid
                                }
                            }
                        }
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.user1

        variables = {
            "guid": self.group_auto.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group_auto.guid)
        self.assertEqual(data["entity"]["members"]["total"], 2) # to users should be added on create
        self.assertEqual(len(data["entity"]["members"]["edges"]), 2)
