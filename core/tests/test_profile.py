from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import UserProfile, ProfileField, UserProfileField, Setting
from user.models import User
from blog.models import Blog
from django.core.cache import cache
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class ProfileTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.profile_field1 = ProfileField.objects.create(
            key="profile_field1",
            name="profile_field1_name"
        )
        self.user_profile_field1 = UserProfileField.objects.create(
            user_profile_id=self.user1.profile.id,
            profile_field_id=self.profile_field1.id,
            value="user_profile_field1_value",
            read_access=[ACCESS_TYPE.public]
        )
        self.profile_field2 = ProfileField.objects.create(
            key="profile_field2",
            name="profile_field2_name",
            category="profile_field2_category",
            field_type="text_field",
            is_editable_by_user=False,
            is_filter=True
        )
        self.user_profile_field2 = UserProfileField.objects.create(
            user_profile_id=self.user1.profile.id,
            profile_field_id=self.profile_field2.id,
            value="user_profile_field2_value",
            read_access=[ACCESS_TYPE.logged_in]
        )
        self.profile_field3 = ProfileField.objects.create(
            key="profile_field3",
            name="profile_field3_name",
            category="profile_field3_category",
            field_type="multi_select_field",
            field_options=['option1', 'option2', 'option3'],
            is_in_overview=True
        )
        self.user_profile_field3 = UserProfileField.objects.create(
            user_profile_id=self.user1.profile.id,
            profile_field_id=self.profile_field3.id,
            value="option1, option2",
            read_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        Setting.objects.create(key='PROFILE', value=[{"key": "profile_field1", "name": "profile_field1_name", "isFilter": False, "isInOverview": False},
                                                     {"key": "profile_field2", "name": "profile_field2_name", "isFilter": False, "isInOverview": False},
                                                     {"key": "profile_field3", "name": "profile_field3_name", "isFilter": False, "isInOverview": True}])


        self.query = """
            query Profile($username: String!) {
                entity(username: $username) {
                    guid
                    status
                    ... on User {
                        name
                        canEdit
                        profile {
                            key
                            name
                            value
                            category
                            accessId
                            fieldType
                            isEditable
                            fieldOptions
                            isFilterable
                            isInOverview
                            __typename
                        }
                        fieldsInOverview {
                            key
                            label
                            value
                        }
                        __typename
                    }
                    __typename
                }
            }

        """

    def tearDown(self):
        self.user_profile_field1.delete()
        self.user_profile_field2.delete()
        self.user_profile_field3.delete()
        self.profile_field1.delete()
        self.profile_field2.delete()
        self.profile_field3.delete()
        self.user2.delete()
        self.user1.delete()
        Setting.objects.all().delete()
        cache.clear()



    def test_get_profile_items_by_owner(self):
        request = HttpRequest()
        request.user = self.user1

        variables = { "username": self.user1.guid}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(len(data["entity"]["profile"]), 3)
        self.assertEqual(data["entity"]["profile"][0]["key"], "profile_field1")
        self.assertEqual(data["entity"]["profile"][0]["name"], "profile_field1_name")
        self.assertEqual(data["entity"]["profile"][0]["value"], "user_profile_field1_value")
        self.assertEqual(data["entity"]["profile"][0]["category"], None)
        self.assertEqual(data["entity"]["profile"][0]["accessId"], 2)
        self.assertEqual(data["entity"]["profile"][0]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][0]["isEditable"], True)
        self.assertEqual(data["entity"]["profile"][0]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][0]["isFilterable"], False)

        self.assertEqual(data["entity"]["profile"][1]["key"], "profile_field2")
        self.assertEqual(data["entity"]["profile"][1]["name"], "profile_field2_name")
        self.assertEqual(data["entity"]["profile"][1]["value"], "user_profile_field2_value")
        self.assertEqual(data["entity"]["profile"][1]["category"], "profile_field2_category")
        self.assertEqual(data["entity"]["profile"][1]["accessId"], 1)
        self.assertEqual(data["entity"]["profile"][1]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][1]["isEditable"], False)
        self.assertEqual(data["entity"]["profile"][1]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][1]["isFilterable"], True)

        self.assertEqual(data["entity"]["profile"][2]["key"], "profile_field3")
        self.assertEqual(data["entity"]["profile"][2]["name"], "profile_field3_name")
        self.assertEqual(data["entity"]["profile"][2]["value"], "option1, option2")
        self.assertEqual(data["entity"]["profile"][2]["accessId"], 0)
        self.assertEqual(data["entity"]["profile"][2]["fieldType"], "multiSelectField")
        self.assertEqual(data["entity"]["profile"][2]["fieldOptions"], ["option1", "option2", "option3"])
        self.assertEqual(data["entity"]["profile"][2]["isFilterable"], True)
        self.assertEqual(data["entity"]["profile"][2]["isInOverview"], True)

        self.assertEqual(data["entity"]["fieldsInOverview"][0]["key"], "profile_field3")


    def test_get_profile_items_by_logged_in_user(self):
        request = HttpRequest()
        request.user = self.user2

        variables = { "username": self.user1.guid}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(len(data["entity"]["profile"]), 3)
        self.assertEqual(data["entity"]["profile"][0]["key"], "profile_field1")
        self.assertEqual(data["entity"]["profile"][0]["name"], "profile_field1_name")
        self.assertEqual(data["entity"]["profile"][0]["value"], "user_profile_field1_value")
        self.assertEqual(data["entity"]["profile"][0]["category"], None)
        self.assertEqual(data["entity"]["profile"][0]["accessId"], 2)
        self.assertEqual(data["entity"]["profile"][0]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][0]["isEditable"], True)
        self.assertEqual(data["entity"]["profile"][0]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][0]["isFilterable"], False)

        self.assertEqual(data["entity"]["profile"][1]["key"], "profile_field2")
        self.assertEqual(data["entity"]["profile"][1]["name"], "profile_field2_name")
        self.assertEqual(data["entity"]["profile"][1]["value"], "user_profile_field2_value")
        self.assertEqual(data["entity"]["profile"][1]["category"], "profile_field2_category")
        self.assertEqual(data["entity"]["profile"][1]["accessId"], 1)
        self.assertEqual(data["entity"]["profile"][1]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][1]["isEditable"], False)
        self.assertEqual(data["entity"]["profile"][1]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][1]["isFilterable"], True)

        self.assertEqual(data["entity"]["profile"][2]["key"], "profile_field3")
        self.assertEqual(data["entity"]["profile"][2]["name"], "profile_field3_name")
        self.assertEqual(data["entity"]["profile"][2]["value"], "")
        self.assertEqual(data["entity"]["profile"][2]["category"], "profile_field3_category")
        self.assertEqual(data["entity"]["profile"][2]["accessId"], 1)
        self.assertEqual(data["entity"]["profile"][2]["fieldType"], "multiSelectField")
        self.assertEqual(data["entity"]["profile"][2]["isEditable"], True)
        self.assertEqual(data["entity"]["profile"][2]["fieldOptions"], ["option1", "option2", "option3"])
        self.assertEqual(data["entity"]["profile"][2]["isFilterable"], True)
        self.assertEqual(data["entity"]["profile"][2]["isInOverview"], True)

        self.assertEqual(data["entity"]["fieldsInOverview"][0]["key"], "profile_field3")

    def test_get_profile_items_by_anonymous_user(self):
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = { "username": self.user1.guid}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)
        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertIsNone(data["entity"])
