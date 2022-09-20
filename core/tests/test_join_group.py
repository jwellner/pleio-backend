from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from unittest import mock


class JoinGroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User, name="a")
        self.group_auto = mixer.blend(Group, owner=self.user1, is_membership_on_request=False, is_auto_membership_enabled=True)

        self.user2 = mixer.blend(User, name="b")  # auto joined to group_auto
        self.user3 = mixer.blend(User, name="c")  # auto joined to group_auto
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

        self.mutation = """
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

    def tearDown(self):
        self.group.delete()
        self.group2.delete()
        self.group_on_request.delete()
        self.group_auto.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

        super().tearDown()

    def test_join_group_anon(self):
        variables = {"group": {"guid": self.group.guid}}

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, variables)

    def test_join_group(self):
        variables = {"group": {"guid": self.group.guid}}

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.mutation, variables)
        data = result['data']['joinGroup']

        self.assertEqual(data["group"]["memberCount"], 1)
        self.assertEqual(data["group"]["members"]["total"], 1)
        self.assertEqual(data["group"]["members"]["edges"][0]["user"]["guid"], self.user1.guid)

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.mutation, variables)
        data = result['data']['joinGroup']

        self.assertEqual(data["group"]["memberCount"], 2)
        self.assertEqual(data["group"]["members"]["total"], 2)
        self.assertEqual(data["group"]["members"]["edges"][0]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["group"]["members"]["edges"][1]["user"]["guid"], self.user2.guid)

        self.assertEqual(self.user1.memberships.filter(group=self.group, type="member").count(), 1)
        self.assertEqual(self.user2.memberships.filter(group=self.group, type="member").count(), 1)

    @mock.patch('core.resolvers.mutation_join_group.schedule_group_access_request_mail')
    def test_join_group_on_request(self, mocked_mail):
        variables = {"group": {"guid": self.group_on_request.guid}}

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.mutation, variables)
        data = result['data']['joinGroup']

        self.assertEqual(data["group"]["memberCount"], 3)
        self.assertEqual(data["group"]["members"]["total"], 3)
        self.assertEqual(mocked_mail.call_count, 3)

        self.graphql_client.force_login(self.user3)
        result = self.graphql_client.post(self.mutation, variables)
        data = result['data']['joinGroup']

        self.assertEqual(data["group"]["memberCount"], 3)
        self.assertEqual(data["group"]["members"]["total"], 3)
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

        variables = {"guid": self.group_auto.guid}

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(query, variables)
        data = result['data']['entity']

        self.assertEqual(data["guid"], self.group_auto.guid)
        self.assertEqual(data["memberCount"], 5)  # to users should be added on create
        self.assertEqual(data["members"]["total"], 5)  # to users should be added on create
        self.assertEqual(len(data["members"]["edges"]), 5)

    def test_join_group_by_member_of_group(self):
        variables = {"group": {"guid": self.group2.guid}}

        with self.assertGraphQlError("already_member_of_group"):
            self.graphql_client.force_login(self.user4)
            self.graphql_client.post(self.mutation, variables)
