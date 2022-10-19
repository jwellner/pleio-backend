from core.models import Group, Subgroup
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class EditSubgroupTestCase(PleioTenantTestCase):

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

        self.subgroup = Subgroup.objects.create(
            name='testSubgroup',
            group=self.group
        )
        self.subgroup.members.add(self.user2)
        self.subgroup.members.add(self.user3)

    def tearDown(self):
        self.subgroup.delete()
        self.group.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.admin.delete()
        super().tearDown()

    def test_edit_subgroup_by_group_owner(self):
        mutation = """
            mutation SubgroupsModal($input: editSubgroupInput!) {
                editSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroupOther",
                "members": [self.user3.guid, self.user4.guid],
                "id": self.subgroup.id
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]

        self.assertEqual(data["editSubgroup"]["success"], True)
        self.assertEqual(Subgroup.objects.get(id=self.subgroup.id).name, 'testSubgroupOther')

    def test_edit_subgroup_by_admin(self):
        mutation = """
            mutation SubgroupsModal($input: editSubgroupInput!) {
                editSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroupOther",
                "members": [self.user3.guid, self.user4.guid],
                "id": self.subgroup.id
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]

        self.assertEqual(data["editSubgroup"]["success"], True)
        self.assertEqual(Subgroup.objects.get(id=self.subgroup.id).name, 'testSubgroupOther')

    def test_edit_subgroup_by_other_user(self):
        mutation = """
            mutation SubgroupsModal($input: editSubgroupInput!) {
                editSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroupOther",
                "members": [self.user3.guid, self.user4.guid],
                "id": self.subgroup.id
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user3)
            self.graphql_client.post(mutation, variables)

    def test_edit_subgroup_by_anonymous(self):
        mutation = """
            mutation SubgroupsModal($input: editSubgroupInput!) {
                editSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroupOther",
                "members": [self.user3.guid, self.user4.guid],
                "id": self.subgroup.id
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_edit_subgroup_with_non_group_member(self):
        mutation = """
            mutation SubgroupsModal($input: editSubgroupInput!) {
                editSubgroup(input: $input) {
                    success
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "name": "testSubgroupOther",
                "members": [self.user3.guid, self.user4.guid],
                "id": self.subgroup.id
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user5)
            self.graphql_client.post(mutation, variables)
