from django.db import connection
from django.test import TestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from mixer.backend.django import mixer
from graphql import GraphQLError

class LeaveGroupTestCase(TestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user1, is_membership_on_request=False)

        self.group.join(self.user1, 'member')
        self.group.join(self.user2, 'owner')

    def tearDown(self):
        self.group.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

    def test_leave_group_anon(self):
        mutation = """
            mutation ($group: leaveGroupInput!) {
                leaveGroup(input: $group) {
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

    def test_leave_group(self):
        mutation = """
            mutation ($group: leaveGroupInput!) {
                leaveGroup(input: $group) {
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
        request.user = self.user3
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_member_of_group")

        request.user = self.user2   
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["leaveGroup"]["group"]["members"]["total"], 1)

        request.user = self.user1
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["leaveGroup"]["group"]["members"]["total"], 0)
