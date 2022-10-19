from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class EditGroupNotificationsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()
        self.group1 = mixer.blend(Group)
        self.group1.join(self.user1)
        self.group1.join(self.user2)

    def tearDown(self):
        self.group1.delete()
        self.admin.delete()
        self.user2.delete()
        self.user1.delete()
        super().tearDown()

    def test_edit_group_notifications_by_owner(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        notificationMode
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "notificationMode": 'direct',
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editGroupNotifications"]["group"]["guid"], self.group1.guid)
        self.assertEqual(data["editGroupNotifications"]["group"]["notificationMode"], 'direct')

    def test_edit_group_notifications_by_admin(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "notificationMode": 'overview',
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        self.graphql_client.post(mutation, variables)

        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        notificationMode
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "notificationMode": 'disable',
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editGroupNotifications"]["group"]["guid"], self.group1.guid)

    def test_edit_group_notifications_by_logged_in_user(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        notificationMode
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "notificationMode": 'disable',
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(mutation, variables)

    def test_edit_group_notifications_by_owner_without_id(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        notificationMode
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "notificationMode": 'overview',
                "guid": self.group1.guid
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editGroupNotifications"]["group"]["guid"], self.group1.guid)
        self.assertEqual(data["editGroupNotifications"]["group"]["notificationMode"], 'overview')

    def test_edit_group_notifications_by_anonymous(self):
        mutation = """
            mutation editGroupNotifications($input: editGroupNotificationsInput!) {
                editGroupNotifications(input: $input) {
                    group {
                        guid
                        notificationMode
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "notificationMode": 'disable',
                "guid": self.group1.guid,
                "userGuid": self.user1.guid
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)
