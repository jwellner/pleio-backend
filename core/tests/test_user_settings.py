from django.db import connection
from core.models import Group
from core.tests.helpers import PleioTenantTestCase, override_config
from user.models import User
from django.core.cache import cache
from mixer.backend.django import mixer


class UserSettingsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.group1 = mixer.blend(Group, owner=self.user2, name='a', auto_notification=True)
        self.group2 = mixer.blend(Group, owner=self.user2, name='b', auto_notification=False)
        self.group1.join(self.user1, 'member')
        self.group2.join(self.user1, 'member')

        self.admin.roles = ['ADMIN']
        self.admin.save()

        self.query = """
            query ProfileSettings($username: String!) {
                entity(username: $username) {
                    guid
                    status
                    ... on User {
                        guid
                        name
                        username
                        canEdit
                        emailNotifications
                        emailNotificationsFrequency
                        isMentionNotificationsEnabled
                        isMentionNotificationPushEnabled
                        isMentionNotificationDirectMailEnabled
                        isCommentNotificationsEnabled
                        isCommentNotificationPushEnabled
                        isCommentNotificationDirectMailEnabled                        
                        getsNewsletter
                        language
                        languageOptions {
                            value
                            label
                        }
                        emailOverview {
                            frequency
                        }
                        requestDelete
                        groupNotifications {
                            guid
                            name
                            isNotificationsEnabled
                            isNotificationDirectMailEnabled
                            isNotificationPushEnabled
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

    def tearDown(self):
        super().tearDown()

    @override_config(EXTRA_LANGUAGES=['en'])
    def test_get_user_settings_by_owner(self):
        """
            User can see own settings
        """

        variables = {"username": self.user1.guid}

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["username"], self.user1.guid)
        self.assertEqual(data["entity"]["emailNotifications"], True)
        self.assertEqual(data["entity"]["isMentionNotificationsEnabled"], True)
        self.assertEqual(data["entity"]["isMentionNotificationDirectMailEnabled"], False)
        self.assertEqual(data["entity"]["isMentionNotificationPushEnabled"], False)
        self.assertEqual(data["entity"]["isCommentNotificationsEnabled"], True)
        self.assertEqual(data["entity"]["isCommentNotificationDirectMailEnabled"], False)
        self.assertEqual(data["entity"]["isCommentNotificationPushEnabled"], False)
        self.assertEqual(data["entity"]["emailNotificationsFrequency"], 4)
        self.assertEqual(data["entity"]["getsNewsletter"], False)
        self.assertEqual(data["entity"]["language"], 'nl')
        self.assertEqual(data["entity"]["languageOptions"], [{'value': 'nl', 'label': 'Nederlands'}, {'value': 'en', 'label': 'English'}])
        self.assertEqual(data["entity"]["emailOverview"]["frequency"], "weekly")
        self.assertEqual(data["entity"]["groupNotifications"][0]["guid"], self.group1.guid)
        self.assertEqual(data["entity"]["groupNotifications"][0]["isNotificationsEnabled"], True)
        self.assertEqual(data["entity"]["groupNotifications"][0]["isNotificationDirectMailEnabled"], False)
        self.assertEqual(data["entity"]["groupNotifications"][0]["isNotificationPushEnabled"], False)
        self.assertEqual(data["entity"]["groupNotifications"][1]["guid"], self.group2.guid)
        self.assertEqual(data["entity"]["groupNotifications"][1]["isNotificationsEnabled"], False)
        self.assertEqual(data["entity"]["groupNotifications"][1]["isNotificationDirectMailEnabled"], False)
        self.assertEqual(data["entity"]["groupNotifications"][1]["isNotificationPushEnabled"], False)
        cache.clear()

    def test_get_user_settings_by_admin(self):
        """
            Admins can see settings of other user
        """
        variables = {
            "username": self.user1.guid
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["username"], self.user1.guid)
        self.assertEqual(data["entity"]["emailNotifications"], True)
        self.assertEqual(data["entity"]["emailNotificationsFrequency"], 4)
        self.assertEqual(data["entity"]["isMentionNotificationsEnabled"], True)
        self.assertEqual(data["entity"]["isMentionNotificationDirectMailEnabled"], False)
        self.assertEqual(data["entity"]["isMentionNotificationPushEnabled"], False)
        self.assertEqual(data["entity"]["isCommentNotificationsEnabled"], True)
        self.assertEqual(data["entity"]["isCommentNotificationDirectMailEnabled"], False)
        self.assertEqual(data["entity"]["isCommentNotificationPushEnabled"], False)
        self.assertEqual(data["entity"]["getsNewsletter"], False)
        self.assertEqual(data["entity"]["language"], 'nl')
        self.assertEqual(data["entity"]["languageOptions"], [{'value': 'nl', 'label': 'Nederlands'}])
        self.assertEqual(data["entity"]["emailOverview"]["frequency"], "weekly")
        self.assertEqual(data["entity"]["groupNotifications"][0]["guid"], self.group1.guid)
        self.assertEqual(data["entity"]["groupNotifications"][0]["isNotificationsEnabled"], True)
        self.assertEqual(data["entity"]["groupNotifications"][0]["isNotificationDirectMailEnabled"], False)
        self.assertEqual(data["entity"]["groupNotifications"][0]["isNotificationPushEnabled"], False)
        self.assertEqual(data["entity"]["groupNotifications"][1]["guid"], self.group2.guid)
        self.assertEqual(data["entity"]["groupNotifications"][1]["isNotificationsEnabled"], False)
        self.assertEqual(data["entity"]["groupNotifications"][1]["isNotificationDirectMailEnabled"], False)
        self.assertEqual(data["entity"]["groupNotifications"][1]["isNotificationPushEnabled"], False)

    def test_get_profile_items_by_logged_in_user(self):
        """
            User can not see settings of other user
        """
        variables = {
            "username": self.user1.guid
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["username"], self.user1.guid)
        self.assertEqual(data["entity"]["emailNotifications"], None)
        self.assertEqual(data["entity"]["emailNotificationsFrequency"], None)
        self.assertEqual(data["entity"]["isMentionNotificationsEnabled"], None)
        self.assertEqual(data["entity"]["isMentionNotificationDirectMailEnabled"], None)
        self.assertEqual(data["entity"]["isMentionNotificationPushEnabled"], None)
        self.assertEqual(data["entity"]["isCommentNotificationsEnabled"], None)
        self.assertEqual(data["entity"]["isCommentNotificationDirectMailEnabled"], None)
        self.assertEqual(data["entity"]["isCommentNotificationPushEnabled"], None)        
        self.assertEqual(data["entity"]["getsNewsletter"], None)
        self.assertEqual(data["entity"]["emailOverview"], None)
        self.assertEqual(data["entity"]["groupNotifications"], [])

    def test_get_profile_items_by_anonymous_user(self):
        """
            Not logged in user can not access User objects
        """
        variables = {
            "username": self.user1.guid
        }

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["username"], self.user1.guid)
        self.assertEqual(data["entity"]["emailNotifications"], None)
        self.assertEqual(data["entity"]["emailNotificationsFrequency"], None)
        self.assertEqual(data["entity"]["isMentionNotificationsEnabled"], None)
        self.assertEqual(data["entity"]["isMentionNotificationDirectMailEnabled"], None)
        self.assertEqual(data["entity"]["isMentionNotificationPushEnabled"], None)
        self.assertEqual(data["entity"]["isCommentNotificationsEnabled"], None)
        self.assertEqual(data["entity"]["isCommentNotificationDirectMailEnabled"], None)
        self.assertEqual(data["entity"]["isCommentNotificationPushEnabled"], None)    
        self.assertEqual(data["entity"]["getsNewsletter"], None)
        self.assertEqual(data["entity"]["emailOverview"], None)
        self.assertEqual(data["entity"]["groupNotifications"], [])
