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

class LeaveGroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user1, is_membership_on_request=False)
        self.mandatory_group = mixer.blend(Group, owner=self.user3, is_membership_on_request=False, is_leaving_group_disabled=True)

        self.group.join(self.user1, 'member')
        self.group.join(self.user2, 'owner')
        self.mandatory_group.join(self.user3, 'member')

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

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request }, logger="test")

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
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_member_of_group")

        request.user = self.user2
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["leaveGroup"]["group"]["members"]["total"], 1)

        request.user = self.user1
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["leaveGroup"]["group"]["members"]["total"], 0)


    def test_leave_mandatory_group(self):
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
                "guid": self.mandatory_group.guid
            }
        }

        request = HttpRequest()
        request.user = self.user3
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "leaving_group_is_disabled")
