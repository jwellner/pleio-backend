from django.core.cache import cache
from django.db import connection
from core.tests.helpers import PleioTenantTestCase, override_config
from user.models import User
from mixer.backend.django import mixer


class EditNotificationsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()

    def tearDown(self):
        super().tearDown()

    @override_config(EXTRA_LANGUAGES=['en'])
    def test_edit_notifications_by_owner(self):
        mutation = """
            mutation editNotifications($input: editNotificationsInput!) {
                editNotifications(input: $input) {
                    user {
                        guid
                        getsNewsletter
                        emailNotifications
                        emailNotificationsFrequency
                        language
                        isMentionNotificationsEnabled
                        isMentionNotificationPushEnabled
                        isMentionNotificationDirectMailEnabled
                        isCommentNotificationsEnabled
                        isCommentNotificationPushEnabled
                        isCommentNotificationDirectMailEnabled
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "emailNotifications": True,
                "isMentionNotificationsEnabled": False,
                "isMentionNotificationDirectMailEnabled": True,
                "isMentionNotificationPushEnabled": True,
                "isCommentNotificationsEnabled": False,
                "isCommentNotificationDirectMailEnabled": True,
                "isCommentNotificationPushEnabled": True,
                "emailNotificationsFrequency": 24,
                "newsletter": True,
                "language": "en"
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editNotifications"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editNotifications"]["user"]["getsNewsletter"], True)
        self.assertEqual(data["editNotifications"]["user"]["emailNotifications"], True)
        self.assertEqual(data["editNotifications"]["user"]["emailNotificationsFrequency"], 24)
        self.assertEqual(data["editNotifications"]["user"]["language"], "en")
        self.assertEqual(data["editNotifications"]["user"]["isMentionNotificationsEnabled"], False)
        self.assertEqual(data["editNotifications"]["user"]["isMentionNotificationDirectMailEnabled"], True)
        self.assertEqual(data["editNotifications"]["user"]["isMentionNotificationPushEnabled"], True)
        self.assertEqual(data["editNotifications"]["user"]["isCommentNotificationsEnabled"], False)
        self.assertEqual(data["editNotifications"]["user"]["isCommentNotificationDirectMailEnabled"], True)
        self.assertEqual(data["editNotifications"]["user"]["isCommentNotificationPushEnabled"], True)

    @override_config(EXTRA_LANGUAGES=['en'])
    def test_edit_notifications_by_admin(self):
        mutation = """
            mutation editNotifications($input: editNotificationsInput!) {
                editNotifications(input: $input) {
                    user {
                        guid
                        getsNewsletter
                        emailNotifications
                        emailNotificationsFrequency
                        language
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "emailNotifications": True,
                "emailNotificationsFrequency": 24,
                "newsletter": False,
                "language": "en"
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editNotifications"]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["editNotifications"]["user"]["getsNewsletter"], False)
        self.assertEqual(data["editNotifications"]["user"]["emailNotifications"], True)
        self.assertEqual(data["editNotifications"]["user"]["emailNotificationsFrequency"], 24)
        self.assertEqual(data["editNotifications"]["user"]["language"], "en")

    @override_config(EXTRA_LANGUAGES=['en'])
    def test_edit_notifications_by_logged_in_user(self):
        mutation = """
            mutation editNotifications($input: editNotificationsInput!) {
                editNotifications(input: $input) {
                    user {
                        guid
                        getsNewsletter
                        emailNotifications
                        emailNotificationsFrequency
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "emailNotifications": True,
                "emailNotificationsFrequency": 24,
                "newsletter": False
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user2)
            self.graphql_client.post(mutation, variables)

    @override_config(EXTRA_LANGUAGES=['en'])
    def test_edit_notifications_by_anonymous(self):
        mutation = """
            mutation editNotifications($input: editNotificationsInput!) {
                editNotifications(input: $input) {
                    user {
                        guid
                        getsNewsletter
                        emailNotifications
                        emailNotificationsFrequency
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "guid": self.user1.guid,
                "emailNotifications": True,
                "emailNotificationsFrequency": 24,
                "newsletter": False
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)
