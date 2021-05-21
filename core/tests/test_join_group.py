from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest import mock

class JoinGroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User, name="a")
        self.group_auto = mixer.blend(Group, owner=self.user1, is_membership_on_request=False, is_auto_membership_enabled=True)

        self.user2 = mixer.blend(User, name="b") # auto joined to group_auto
        self.user3 = mixer.blend(User, name="c") # auto joined to group_auto
        self.user4 = mixer.blend(User, name="d")
        self.groupAdmin1 = mixer.blend(User, name="e")
        self.groupAdmin2 = mixer.blend(User, name="f")
        self.group = mixer.blend(Group, owner=self.user1, is_membership_on_request=False, welcome_message='welcome_message')
        self.group2 = mixer.blend(Group, owner=self.user1, is_membership_on_request=False, welcome_message='<p> </p>  ')

        self.group_on_request = mixer.blend(Group, owner=self.user1, is_membership_on_request=True)
        self.group_on_request.join(self.user1, member_type='owner')
        self.group_on_request.join(self.groupAdmin1, member_type='admin')
        self.group_on_request.join(self.groupAdmin2, member_type='admin')
        self.group2.join(self.user4, 'member')

    def tearDown(self):
        self.group.delete()
        self.group2.delete()
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

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    def test_join_group(self):
        mutation = """
            mutation ($group: joinGroupInput!) {
                joinGroup(input: $group) {
                    group {
                        memberCount
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
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["joinGroup"]["group"]["memberCount"], 1)
        self.assertEqual(data["joinGroup"]["group"]["members"]["total"], 1)
        self.assertEqual(data["joinGroup"]["group"]["members"]["edges"][0]["user"]["guid"], self.user1.guid)

        request.user = self.user2
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["joinGroup"]["group"]["memberCount"], 2)
        self.assertEqual(data["joinGroup"]["group"]["members"]["total"], 2)
        self.assertEqual(data["joinGroup"]["group"]["members"]["edges"][0]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["joinGroup"]["group"]["members"]["edges"][1]["user"]["guid"], self.user2.guid)

        self.assertEqual(self.user1.memberships.filter(group=self.group, type="member").count(), 1)
        self.assertEqual(self.user2.memberships.filter(group=self.group, type="member").count(), 1)

    @mock.patch('core.resolvers.mutation_join_group.send_mail_multi.delay')
    def test_join_group_on_request(self, mocked_send_mail_multi):
        mutation = """
            mutation ($group: joinGroupInput!) {
                joinGroup(input: $group) {
                    group {
                        memberCount
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

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["joinGroup"]["group"]["memberCount"], 3)
        self.assertEqual(data["joinGroup"]["group"]["members"]["total"], 3)
        self.assertEqual(mocked_send_mail_multi.call_count, 3)

        request.user = self.user3
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["joinGroup"]["group"]["memberCount"], 3)
        self.assertEqual(data["joinGroup"]["group"]["members"]["total"], 3)
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
                        memberCount
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

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group_auto.guid)
        self.assertEqual(data["entity"]["memberCount"], 5) # to users should be added on create
        self.assertEqual(data["entity"]["members"]["total"], 5) # to users should be added on create
        self.assertEqual(len(data["entity"]["members"]["edges"]), 5)


    def test_join_group_by_member_of_group(self):
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
                "guid": self.group2.guid
            }
        }

        request = HttpRequest()
        request.user = self.user4
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "already_member_of_group")

    @mock.patch('core.tasks.send_mail_multi.delay')
    def test_welcome_message(self, mock_send_mail_multi):
        mutation = """
            mutation ($group: joinGroupInput!) {
                joinGroup(input: $group) {
                    group {
                        memberCount
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
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        mock_send_mail_multi.assert_called_once()

    @mock.patch('core.tasks.send_mail_multi.delay')
    def test_no_welcome_message(self, mock_send_mail_multi):
        mutation = """
            mutation ($group: joinGroupInput!) {
                joinGroup(input: $group) {
                    group {
                        memberCount
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
                "guid": self.group2.guid
            }
        }
        request = HttpRequest()
        request.user = self.user1
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        mock_send_mail_multi.assert_not_called()
