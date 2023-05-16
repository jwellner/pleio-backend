from core.factories import GroupFactory
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory

class ChangeGroupRoleTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory(email='user1@example.com')
        self.user2 = UserFactory(email='user2@example.com')
        self.user3 = UserFactory(email='user3@example.com')
        self.user4 = UserFactory(email='user4@example.com')
        self.admin = AdminFactory(email='admin@example.com')
        self.group1 = GroupFactory(name="Group1", owner=self.user1)
        self.group1.join(self.user2, 'member')
        self.group1.join(self.user4, 'admin')

        self.mutation = """
            mutation removeMembers($input: removeGroupMembersInput!) {
                removeGroupMembers(input: $input) {
                    group {
                        guid
                    }
                }
            }        
        """

    def tearDown(self):
        super().tearDown()

    def test_remove_group_members_by_owner(self):

        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuids": [self.user2.guid, self.user4.guid]                 
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.mutation, variables)
        data = result["data"]["removeGroupMembers"]

        self.assertEqual(data["group"]["guid"], self.group1.guid)
        self.assertFalse(self.group1.is_member(self.user2))
    
    def test_remove_group_members_by_admin(self):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuids": [self.user2.guid, self.user4.guid]                 
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)
        data = result["data"]["removeGroupMembers"]

        self.assertEqual(data["group"]["guid"], self.group1.guid)

    def test_remove_non_member_of_group(self):
        variables = {
            "input": {
                "guid": self.group1.guid,
                "userGuids": [self.user2.guid, self.user3.guid]                 
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(self.mutation, variables)

        self.assertFalse(self.group1.is_member(self.user2))
        self.assertFalse(self.group1.is_member(self.user3))
