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
        self.authenticatedUser = mixer.blend(User, name="yy")
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User, name="aa")
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User, name="xx")
        self.user5 = mixer.blend(User, name="yyy")
        self.user6 = mixer.blend(User, name="zz")
        self.userAdmin = mixer.blend(User, roles=["ADMIN"])
        self.group = mixer.blend(Group, owner=self.authenticatedUser, introduction='introductionMessage')
        self.group.join(self.authenticatedUser, 'owner')
        self.group.join(self.user2, 'member')
        self.group.join(self.user3, 'pending')
        self.group.join(self.user4, 'admin')
        self.group.join(self.user6, 'admin')

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
                        invited (limit:1){
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

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["invited"]["total"], 2)
        self.assertEqual(len(data["entity"]["invited"]["edges"]), 1)


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

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["__typename"], "Group")
        self.assertEqual(data["entity"]["invite"]["total"], 3)
        self.assertEqual(len(data["entity"]["invite"]["edges"]), 3)

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

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

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

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["__typename"], "Group")
        self.assertEqual(data["entity"]["membershipRequests"]["total"], 1)
        self.assertEqual(data["entity"]["membershipRequests"]["edges"][0]["guid"], self.user3.guid)


    def test_entity_group_memberlist(self):
        query = """
            query MembersList($guid: String!, $q: String, $offset: Int) {
                entity(guid: $guid) {
                    ... on Group {
                        guid
                        members(q: $q, offset: $offset, limit: 20) {
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
                                }
                            }
                        }
                    }
                }
            }

        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.group.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["members"]["total"], 4)
        self.assertEqual(len(data["entity"]["members"]["edges"]), 4)
        self.assertEqual(data["entity"]["members"]["edges"][0]["role"], "owner")
        self.assertEqual(data["entity"]["members"]["edges"][1]["role"], "admin")

    def test_group_hidden_introduction(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        introduction
                    }
                }
            }

        """
        request = HttpRequest()
        request.user = self.user5

        variables = {
            "guid": self.group.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["introduction"], "")

    def test_group_can_change_ownership_member_owner(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        canChangeOwnership
                    }
                }
            }

        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.group.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["canChangeOwnership"], True)

    def test_group_can_change_ownership_member_admin(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        canChangeOwnership
                    }
                }
            }

        """
        request = HttpRequest()
        request.user = self.user4

        variables = {
            "guid": self.group.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["canChangeOwnership"], False)

    def test_group_can_change_ownership_site_admin(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        canChangeOwnership
                    }
                }
            }

        """
        request = HttpRequest()
        request.user = self.userAdmin

        variables = {
            "guid": self.group.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["canChangeOwnership"], True)
