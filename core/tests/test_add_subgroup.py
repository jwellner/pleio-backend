from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from mixer.backend.django import mixer


class AddSubgroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory(name='a')
        self.user2 = UserFactory(name='b')
        self.user3 = UserFactory(name='c')
        self.user4 = UserFactory(name='d')
        self.admin = AdminFactory()

        self.group = mixer.blend(Group, owner=self.user1)
        self.group.join(self.user2, 'member')
        self.group.join(self.user4, 'member')

    def test_add_subgroup_by_group_owner(self):
        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [self.user2.guid, self.user4.guid],
                "groupGuid": self.group.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["addSubgroup"]["success"], True)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].name, 'testSubgroup')
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].members.filter(id=self.user2.guid)[0], self.user2)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].members.filter(id=self.user4.guid)[0], self.user4)

    def test_add_subgroup_by_admin(self):
        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [self.user2.guid],
                "groupGuid": self.group.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["addSubgroup"]["success"], True)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].name, 'testSubgroup')
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0].members.all()[0], self.user2)

    def test_add_subgroup_by_group_member(self):
        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [],
                "groupGuid": self.group.guid
            }
        }

        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(mutation, variables)

    def test_add_subgroup_by_anonymous(self):
        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [self.user2.guid],
                "groupGuid": self.group.guid
            }
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(mutation, variables)

    def test_add_subgroup_with_non_group_member(self):
        mutation = """
            mutation SubgroupsModal($input: addSubgroupInput!) {
                addSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroup",
                "members": [self.user3.guid],
                "groupGuid": self.group.guid
            }
        }

        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(mutation, variables)
