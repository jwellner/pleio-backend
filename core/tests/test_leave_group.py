from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class LeaveGroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.user1, is_membership_on_request=False)
        self.mandatory_group = mixer.blend(Group, owner=self.user3, is_membership_on_request=False, is_leaving_group_disabled=True)

        self.group.join(self.user1, 'member')
        self.group.join(self.user2, 'owner')
        self.mandatory_group.join(self.user3, 'member')

    def tearDown(self):
        super().tearDown()

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

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("user_not_member_of_group"):
            self.graphql_client.force_login(self.user3)
            self.graphql_client.post(mutation, variables)

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["leaveGroup"]["group"]["members"]["total"], 1)

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        with self.assertGraphQlError("leaving_group_is_disabled"):
            self.graphql_client.force_login(self.user3)
            self.graphql_client.post(mutation, variables)
