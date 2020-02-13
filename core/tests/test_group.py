from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group, GroupInvitation
from user.models import User
from file.models import FileFolder
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class GroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser)
        self.group.join(self.user2, 'member')
        self.group.join(self.user3, 'pending')
        self.file = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            is_folder=False,
            parent=None,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.invitation = GroupInvitation.objects.create(code="7d97cea90c83722c7262", invited_user=self.user1, group=self.group)
        self.invitation = GroupInvitation.objects.create(code="7d97cea90c83722c7262", invited_user=self.user3, group=self.group)

    def tearDown(self):
        self.group.delete()
        self.file.delete()
        self.user1.delete()
        self.user2 = mixer.blend(User)
        self.authenticatedUser.delete()


    def test_entity_group_invited_list(self):
        query = """
            query InvitedList($guid: String!) {
                entity(guid: $guid) {
                    guid
                    ... on Group {
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
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "guid": self.group.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["__typename"], "Group")
        self.assertEqual(data["entity"]["invited"]["total"], 2)
        self.assertEqual(data["entity"]["invited"]["edges"][0]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["entity"]["invited"]["edges"][0]["email"], self.user1.email)


    def test_entity_group_invite_list(self):
        query = """
            query InviteAutoCompleteList($guid: String!, $q: String) {
                entity(guid: $guid) {
                    guid
                    ... on Group {
                        invite(q: $q) {
                            total
                            edges {
                                invited
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
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "guid": self.group.guid,
            "q": ""
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["__typename"], "Group")
        self.assertEqual(data["entity"]["invite"]["total"], 1)
        self.assertEqual(data["entity"]["invite"]["edges"][0]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["entity"]["invite"]["edges"][0]["invited"], False)

    def test_entity_group_invite_list_empty(self):
        query = """
            query InviteAutoCompleteList($guid: String!, $q: String) {
                entity(guid: $guid) {
                    guid
                    ... on Group {
                        invite(q: $q) {
                            total
                            edges {
                                invited
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
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.group.guid,
            "q": "DFWETCCVSDFFSDGSER43254457453tqertq345"
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["__typename"], "Group")
        self.assertEqual(data["entity"]["invite"]["total"], 0)

    def test_entity_group_membership_request_list(self):
        query = """
            query MembershipRequestsList($guid: String!) {
                entity(guid: $guid) {
                    guid
                    ... on Group {
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
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.group.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["__typename"], "Group")
        self.assertEqual(data["entity"]["membershipRequests"]["total"], 1)
        self.assertEqual(data["entity"]["membershipRequests"]["edges"][0]["guid"], self.user3.guid)
