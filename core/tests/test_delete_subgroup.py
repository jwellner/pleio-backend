from core.models import Group, Subgroup
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class DeleteSubgroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User)
        self.user5 = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.user1)
        self.group.join(self.user2, 'member')
        self.group.join(self.user3, 'member')
        self.group.join(self.user4, 'member')

        self.subgroup1 = Subgroup.objects.create(
            name='testSubgroup1',
            group=self.group
        )
        self.subgroup1.members.add(self.user2)
        self.subgroup1.members.add(self.user3)

        self.subgroup2 = Subgroup.objects.create(
            name='testSubgroup2',
            group=self.group
        )
        self.subgroup2.members.add(self.user2)
        self.subgroup2.members.add(self.user4)

    def tearDown(self):
        super().tearDown()

    def test_delete_subgroup_by_group_owner(self):
        mutation = """
            mutation SubgroupItem($input: deleteSubgroupInput!) {
                deleteSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "id": self.subgroup1.id
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["deleteSubgroup"]["success"], True)
        self.assertEqual(len(Group.objects.get(id=self.group.id).subgroups.all()), 1)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0], self.subgroup2)

    def test_delete_subgroup_by_admin(self):
        mutation = """
            mutation SubgroupItem($input: deleteSubgroupInput!) {
                deleteSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "id": self.subgroup1.id
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["deleteSubgroup"]["success"], True)
        self.assertEqual(len(Group.objects.get(id=self.group.id).subgroups.all()), 1)
        self.assertEqual(Group.objects.get(id=self.group.id).subgroups.all()[0], self.subgroup2)

    def test_delete_subgroup_by_other_user(self):
        mutation = """
            mutation SubgroupItem($input: deleteSubgroupInput!) {
                deleteSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "id": self.subgroup1.id
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user3)
            self.graphql_client.post(mutation, variables)

    def test_delete_subgroup_by_anonymous(self):
        mutation = """
            mutation SubgroupItem($input: deleteSubgroupInput!) {
                deleteSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "id": self.subgroup1.id
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)
