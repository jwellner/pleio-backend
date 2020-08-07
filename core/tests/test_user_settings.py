from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group, UserProfile, ProfileField, UserProfileField
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class UserSettingsTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.group1 = mixer.blend(Group, owner=self.user2, name='a')
        self.group2 = mixer.blend(Group, owner=self.user2, name='b')
        self.group1.join(self.user1, 'member')
        self.group2.join(self.user1, 'member')

        self.group1.set_member_notification(self.user1, True)

        self.admin.is_admin = True
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
                        getsNewsletter
                        emailOverview {
                            frequency
                        }
                        requestDelete
                        groupNotifications {
                            guid
                            name
                            getsNotifications
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

    def tearDown(self):
        self.group1.delete()
        self.group2.delete()
        self.user2.delete()
        self.user1.delete()


    def test_get_user_settings_by_owner(self):
        """
            User can see own settings
        """
        request = HttpRequest()
        request.user = self.user1

        variables = { "username": self.user1.guid}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["username"], self.user1.guid)
        self.assertEqual(data["entity"]["emailNotifications"], False)
        self.assertEqual(data["entity"]["getsNewsletter"], False)
        self.assertEqual(data["entity"]["emailOverview"]["frequency"], "weekly")
        self.assertEqual(data["entity"]["groupNotifications"][0]["guid"], self.group1.guid)
        self.assertEqual(data["entity"]["groupNotifications"][0]["getsNotifications"], True)
        self.assertEqual(data["entity"]["groupNotifications"][1]["guid"], self.group2.guid)
        self.assertEqual(data["entity"]["groupNotifications"][1]["getsNotifications"], False)


    def test_get_user_settings_by_admin(self):
        """
            Admins can see settings of other user
        """
        request = HttpRequest()
        request.user = self.admin

        variables = { "username": self.user1.guid}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["username"], self.user1.guid)
        self.assertEqual(data["entity"]["emailNotifications"], False)
        self.assertEqual(data["entity"]["getsNewsletter"], False)
        self.assertEqual(data["entity"]["emailOverview"]["frequency"], "weekly")
        self.assertEqual(data["entity"]["groupNotifications"][0]["guid"], self.group1.guid)
        self.assertEqual(data["entity"]["groupNotifications"][0]["getsNotifications"], True)
        self.assertEqual(data["entity"]["groupNotifications"][1]["guid"], self.group2.guid)
        self.assertEqual(data["entity"]["groupNotifications"][1]["getsNotifications"], False)

    def test_get_profile_items_by_logged_in_user(self):
        """
            User can not see settings of other user
        """
        request = HttpRequest()
        request.user = self.user2

        variables = { "username": self.user1.guid}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["username"], self.user1.guid)
        self.assertEqual(data["entity"]["emailNotifications"], None)
        self.assertEqual(data["entity"]["getsNewsletter"], None)
        self.assertEqual(data["entity"]["emailOverview"], None)
        self.assertEqual(data["entity"]["groupNotifications"], [])

    def test_get_profile_items_by_anonymous_user(self):
        """
            Not logged in user can not access User objects
        """
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = { "username": self.user1.guid}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertIsNone(data["entity"])
