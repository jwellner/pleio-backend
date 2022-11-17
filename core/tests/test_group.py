from sysconfig import is_python_build
from unittest import mock

from core.models import Group, GroupInvitation
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from user.models import User
from file.models import FileFolder
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class GroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.authenticatedUser = mixer.blend(User, name="yy")
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User, name="aa")
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User, name="xx")
        self.user5 = mixer.blend(User, name="yyy")
        self.user6 = mixer.blend(User, name="zz")
        self.inactive_user = mixer.blend(User, name="inactive", is_active=False)
        self.userAdmin = mixer.blend(User, roles=["ADMIN"])
        self.group = mixer.blend(Group, owner=self.authenticatedUser, introduction='introductionMessage')
        self.group.join(self.authenticatedUser, 'owner')
        self.group.join(self.user2, 'member')
        self.group.join(self.user3, 'pending')
        self.group.join(self.user4, 'admin')
        self.group.join(self.user6, 'admin')
        self.group.join(self.inactive_user)
        self.hidden_group = mixer.blend(Group, owner=self.authenticatedUser, is_hidden=True)


        self.file = FileFolder.objects.create(
            owner=self.authenticatedUser,
            upload=None,
            type=FileFolder.Types.FILE,
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
        super().tearDown()

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
        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
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
        variables = {
            "guid": self.group.guid,
            "q": ""
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
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
        variables = {
            "guid": self.group.guid,
            "q": "DFWETCCVSDFFSDGSER43254457453tqertq345"
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
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
        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
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
                        memberCount
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
        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["memberCount"], 4)
        self.assertEqual(data["entity"]["members"]["total"], 4)
        self.assertEqual(len(data["entity"]["members"]["edges"]), 4)
        self.assertEqual(data["entity"]["members"]["edges"][0]["role"], "owner")
        self.assertEqual(data["entity"]["members"]["edges"][1]["role"], "admin")

    def test_group_is_hidden_by_admin(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        guid
                    }
                }
            }

        """
        variables = {
            "guid": self.hidden_group.guid
        }

        self.graphql_client.force_login(self.userAdmin)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], str(self.hidden_group.id))

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
        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.user5)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["introduction"], "")

    def test_group_can_change_ownership_member_owner(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        canChangeOwnership
                        memberRole
                    }
                }
            }

        """
        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["canChangeOwnership"], True)
        self.assertEqual(data["entity"]["memberRole"], 'owner')

    def test_group_can_change_ownership_member_admin(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        canChangeOwnership
                        memberRole
                    }
                }
            }

        """
        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.user4)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["canChangeOwnership"], False)
        self.assertEqual(data["entity"]["memberRole"], 'admin')

    def test_group_can_change_ownership_site_admin(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        canChangeOwnership
                        memberRole
                    }
                }
            }

        """
        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.userAdmin)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["canChangeOwnership"], True)
        self.assertEqual(data["entity"]["memberRole"], None)

    def test_group_cannot_change_ownership_anonymous(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        canChangeOwnership
                        memberRole
                    }
                }
            }

        """
        variables = {
            "guid": self.group.guid
        }

        result = self.graphql_client.post(query, variables)
        data = result["data"]

        self.assertEqual(data["entity"]["canChangeOwnership"], False)
        self.assertEqual(data["entity"]["memberRole"], None)

    def test_pending_group_member_can_view_group(self):
        query = """
            query Group($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        canChangeOwnership
                        memberRole
                    }
                }
            }
        """
        variables = {
            "guid": self.group.guid
        }

        self.graphql_client.force_login(self.user3)
        result = self.graphql_client.post(query, variables)
        self.assertEqual(result['data']['entity']['memberRole'], 'pending')

    inaccessible_field = ["members", "invite", "invited", "membershipRequests"]

    def test_unaccessible_data_for_unauthenticated_user(self):
        for field in self.inaccessible_field:
            with self.subTest():
                query = """
                    query Group($guid: String!) {{
                        entity(guid: $guid) {{
                            ... on Group {{
                                {field} {{ total }}
                            }}
                        }}
                    }}
                """.format(field=field)

                variables = {
                    "guid": self.group.guid
                }

                self.graphql_client.reset()
                result = self.graphql_client.post(query, variables)

                self.assertEqual(result["data"]["entity"][field]["total"], 0)

    def test_join_a_group_triggers_refresh_index(self):
        query = """
        mutation AddMemberToGroup($input: joinGroupInput!) {
            joinGroup(input: $input) {
                group {
                    memberRole
                }
            }
        }
        """

        user = UserFactory()
        self.graphql_client.force_login(user)

        with mock.patch('core.elasticsearch.schedule_index_document') as index_document:
            result = self.graphql_client.post(query, {'input': {
                'guid': self.group.guid
            }})

            self.assertEqual(result['data']['joinGroup']['group']['memberRole'], 'member')
            assert index_document.called_with(user)

    def test_leave_a_group_triggers_refresh_index(self):
        query = """
        mutation RemoveMemberToGroup($input: leaveGroupInput!) {
            leaveGroup(input: $input) {
                group {
                    memberRole
                }
            }
        }
        """

        user = UserFactory()
        self.graphql_client.force_login(user)
        self.group.join(user)

        with mock.patch('core.elasticsearch.schedule_index_document') as index_document:
            result = self.graphql_client.post(query, {'input': {
                'guid': self.group.guid
            }})

            self.assertIsNone(result['data']['leaveGroup']['group']['memberRole'])
            assert index_document.called_with(user)
