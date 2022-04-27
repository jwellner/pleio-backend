from django.core.exceptions import ValidationError
from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import ProfileField, UserProfileField, Group, GroupProfileFieldSetting
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
            name="profile_field1_name",
            is_on_vcard=True
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
            # category="profile_field2_category",
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
            # category="profile_field3_category",
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

        self.profile_field4 = ProfileField.objects.create(
            key="profile_field4",
            name="profile_field4_name"
        )

        self.profile_field5 = ProfileField.objects.create(
            key="profile_field5",
            name="profile_field5_name"
        )

        self.group = mixer.blend(Group)

        GroupProfileFieldSetting.objects.create(
            profile_field=self.profile_field2,
            group=self.group,
            show_field=True
        )

        cache.set("%s%s" % (connection.schema_name, 'PROFILE_SECTIONS'), [
            {"name": "", "profileFieldGuids": [str(self.profile_field1.id), str(self.profile_field5.id)]},
            {"name": "section_one", "profileFieldGuids": [str(self.profile_field3.id)]},
            {"name": "section_two", "profileFieldGuids": [str(self.profile_field2.id)]}
        ])

        self.query = """
            query Profile($username: String!, $groupGuid: String) {
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
                        vcard {
                            key
                            name
                            value
                            accessId
                            __typename
                        }
                        fieldsInOverview(groupGuid: $groupGuid) {
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
        self.profile_field4.delete()
        self.profile_field5.delete()
        self.user2.delete()
        self.user1.delete()
        cache.clear()

    def test_get_profile_items_by_owner(self):
        request = HttpRequest()
        request.user = self.user1

        variables = {"username": self.user1.guid}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(len(data["entity"]["profile"]), 4)
        self.assertEqual(data["entity"]["profile"][0]["key"], "profile_field1")
        self.assertEqual(data["entity"]["profile"][0]["name"], "profile_field1_name")
        self.assertEqual(data["entity"]["profile"][0]["value"], "user_profile_field1_value")
        self.assertEqual(data["entity"]["profile"][0]["category"], "")
        self.assertEqual(data["entity"]["profile"][0]["accessId"], 2)
        self.assertEqual(data["entity"]["profile"][0]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][0]["isEditable"], True)
        self.assertEqual(data["entity"]["profile"][0]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][0]["isFilterable"], False)

        self.assertEqual(data["entity"]["profile"][3]["key"], "profile_field2")
        self.assertEqual(data["entity"]["profile"][3]["name"], "profile_field2_name")
        self.assertEqual(data["entity"]["profile"][3]["value"], "user_profile_field2_value")
        self.assertEqual(data["entity"]["profile"][3]["category"], "section_two")
        self.assertEqual(data["entity"]["profile"][3]["accessId"], 1)
        self.assertEqual(data["entity"]["profile"][3]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][3]["isEditable"], False)
        self.assertEqual(data["entity"]["profile"][3]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][3]["isFilterable"], True)

        self.assertEqual(data["entity"]["profile"][2]["key"], "profile_field3")
        self.assertEqual(data["entity"]["profile"][2]["name"], "profile_field3_name")
        self.assertEqual(data["entity"]["profile"][2]["value"], "option1, option2")
        self.assertEqual(data["entity"]["profile"][2]["category"], "section_one")
        self.assertEqual(data["entity"]["profile"][2]["accessId"], 0)
        self.assertEqual(data["entity"]["profile"][2]["fieldType"], "multiSelectField")
        self.assertEqual(data["entity"]["profile"][2]["fieldOptions"], ["option1", "option2", "option3"])
        self.assertEqual(data["entity"]["profile"][2]["isFilterable"], True)
        self.assertEqual(data["entity"]["profile"][2]["isInOverview"], True)

        self.assertEqual(data['entity']['vcard'][0]['key'], 'profile_field1')
        self.assertEqual(data['entity']['vcard'][0]['name'], 'profile_field1_name')
        self.assertEqual(data['entity']['vcard'][0]['value'], 'user_profile_field1_value')
        self.assertEqual(data['entity']['vcard'][0]['accessId'], 2)

        self.assertEqual(data["entity"]["fieldsInOverview"][0]["key"], "profile_field3")

    def test_get_profile_items_by_logged_in_user(self):
        request = HttpRequest()
        request.user = self.user2

        variables = {"username": self.user1.guid}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(len(data["entity"]["profile"]), 4)
        self.assertEqual(data["entity"]["profile"][0]["key"], "profile_field1")
        self.assertEqual(data["entity"]["profile"][0]["name"], "profile_field1_name")
        self.assertEqual(data["entity"]["profile"][0]["value"], "user_profile_field1_value")
        self.assertEqual(data["entity"]["profile"][0]["category"], "")
        self.assertEqual(data["entity"]["profile"][0]["accessId"], 2)
        self.assertEqual(data["entity"]["profile"][0]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][0]["isEditable"], True)
        self.assertEqual(data["entity"]["profile"][0]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][0]["isFilterable"], False)

        self.assertEqual(data["entity"]["profile"][3]["key"], "profile_field2")
        self.assertEqual(data["entity"]["profile"][3]["name"], "profile_field2_name")
        self.assertEqual(data["entity"]["profile"][3]["value"], "user_profile_field2_value")
        self.assertEqual(data["entity"]["profile"][3]["category"], "section_two")
        self.assertEqual(data["entity"]["profile"][3]["accessId"], 1)
        self.assertEqual(data["entity"]["profile"][3]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][3]["isEditable"], False)
        self.assertEqual(data["entity"]["profile"][3]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][3]["isFilterable"], True)

        self.assertEqual(data["entity"]["profile"][2]["key"], "profile_field3")
        self.assertEqual(data["entity"]["profile"][2]["name"], "profile_field3_name")
        self.assertEqual(data["entity"]["profile"][2]["value"], "")
        self.assertEqual(data["entity"]["profile"][2]["category"], "section_one")
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

        variables = {"username": self.user1.guid}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})
        self.assertTrue(result[0])

        data = result[1]["data"]

        # should be able to view public provile data
        self.assertEqual(len(data["entity"]["profile"]), 4)
        self.assertEqual(data["entity"]["profile"][0]["key"], "profile_field1")
        self.assertEqual(data["entity"]["profile"][0]["name"], "profile_field1_name")
        self.assertEqual(data["entity"]["profile"][0]["value"], "user_profile_field1_value")
        self.assertEqual(data["entity"]["profile"][0]["category"], "")
        self.assertEqual(data["entity"]["profile"][0]["accessId"], 2)
        self.assertEqual(data["entity"]["profile"][0]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][0]["isEditable"], True)
        self.assertEqual(data["entity"]["profile"][0]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][0]["isFilterable"], False)

        self.assertEqual(data["entity"]["profile"][3]["key"], "profile_field2")
        self.assertEqual(data["entity"]["profile"][3]["name"], "profile_field2_name")
        self.assertEqual(data["entity"]["profile"][3]["value"], "")
        self.assertEqual(data["entity"]["profile"][3]["category"], "section_two")
        self.assertEqual(data["entity"]["profile"][3]["accessId"], 1)
        self.assertEqual(data["entity"]["profile"][3]["fieldType"], "textField")
        self.assertEqual(data["entity"]["profile"][3]["isEditable"], False)
        self.assertEqual(data["entity"]["profile"][3]["fieldOptions"], [])
        self.assertEqual(data["entity"]["profile"][3]["isFilterable"], True)

        self.assertEqual(data["entity"]["profile"][2]["key"], "profile_field3")
        self.assertEqual(data["entity"]["profile"][2]["name"], "profile_field3_name")
        self.assertEqual(data["entity"]["profile"][2]["value"], "")
        self.assertEqual(data["entity"]["profile"][2]["category"], "section_one")
        self.assertEqual(data["entity"]["profile"][2]["accessId"], 1)
        self.assertEqual(data["entity"]["profile"][2]["fieldType"], "multiSelectField")
        self.assertEqual(data["entity"]["profile"][2]["isEditable"], True)
        self.assertEqual(data["entity"]["profile"][2]["fieldOptions"], ["option1", "option2", "option3"])
        self.assertEqual(data["entity"]["profile"][2]["isFilterable"], True)
        self.assertEqual(data["entity"]["profile"][2]["isInOverview"], True)

    def test_user_fields_in_group_overview(self):
        request = HttpRequest()
        request.user = self.user2

        variables = {"username": self.user1.guid, "groupGuid": self.group.guid}

        result = graphql_sync(schema, {"query": self.query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["fieldsInOverview"][0]["key"], "profile_field2")

    def test_profile_field_html_not_allowed_icm_is_filter(self):
        field = ProfileField.objects.create(key="demo", name="demo", field_type='html_field')
        with self.assertRaises(ValidationError):
            field.is_filter = True
            field.save()

    def test_profile_field_html_not_allowed_icm_in_overview(self):
        field = ProfileField.objects.create(key="demo", name="demo", field_type='html_field')
        with self.assertRaises(ValidationError):
            field.is_in_overview = True
            field.save()

    def test_profile_field_html_not_allowed_icm_vcard(self):
        field = ProfileField.objects.create(key="demo", name="profile_field", field_type='html_field')

        with self.assertRaises(ValidationError):
            field.is_on_vcard = True
            field.save()
