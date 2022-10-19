from django.core.exceptions import ValidationError
from django.db import connection
from core.models import ProfileField, UserProfileField, Group, GroupProfileFieldSetting
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from django.core.cache import cache
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class ProfileTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
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
        super().tearDown()

    def test_get_profile_items_by_owner(self):
        variables = {"username": self.user1.guid}

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
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
        self.assertEqual(data["entity"]["profile"][2]["value"], "option1,option2")
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
        variables = {"username": self.user1.guid}

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
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
        variables = {"username": self.user1.guid}

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
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
        variables = {"username": self.user1.guid, "groupGuid": self.group.guid}

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["fieldsInOverview"][0]["key"], "profile_field2")

    def test_profile_field_is_not_on_vcard_when_empty(self):
        clean_user = mixer.blend(User)
        field = UserProfileField.objects.create(
            user_profile_id=clean_user.profile.id,
            profile_field_id=self.profile_field1.id,
            read_access=[ACCESS_TYPE.public],
            value="has value!",
        )

        self.graphql_client.force_login(clean_user)
        variables = {"username": clean_user.guid, "groupGuid": self.group.guid}
        result = self.graphql_client.post(self.query, variables)

        # Value exists, so profile_field exists.
        data = result.get('data')
        self.assertIsNotNone(data['entity']['vcard'])
        self.assertIn(self.profile_field1.key, [v['key'] for v in data['entity']['vcard']])

        field.value = ""
        field.save()

        # value is empty, so profile_field is not in the result.
        variables = {"username": clean_user.guid, "groupGuid": self.group.guid}
        result = self.graphql_client.post(self.query, variables)

        data = result.get('data')
        self.assertIsNotNone(data['entity']['vcard'])
        self.assertNotIn(self.profile_field1.key, [v['key'] for v in data['entity']['vcard']])

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

    def test_profile_field_when_multi_select_values_change(self):
        self.profile_field3.field_options = ['option2', 'option3']
        self.profile_field3.save()

        self.graphql_client.force_login(self.user1)
        variables = {"username": self.user1.guid}
        result = self.graphql_client.post(self.query, variables)

        profile_item = UserProfileField.objects.get(user_profile=self.user1.profile, profile_field=self.profile_field3)
        self.assertIn('option1', profile_item.value)
        self.assertIn('option2', profile_item.value)

        profile_values = {p['key']: p['value'] for p in result['data']['entity']['profile']}
        self.assertNotIn('option1', profile_values[self.profile_field3.key])
        self.assertIn('option2', profile_values[self.profile_field3.key])
