from backend2.schema import schema
from ariadne import graphql_sync

from core.constances import ACCESS_TYPE
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, ProfileField, Setting, GroupProfileFieldSetting, UserProfileField, UserProfile
from core.tests.helpers import ElasticsearchTestCase
from user.models import User
from mixer.backend.django import mixer


class FiltersTestCase(ElasticsearchTestCase):

    def setUp(self):
        super().setUp()

        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.other = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()

        self.profile_field1 = ProfileField.objects.create(key='text_key', name='text_name', field_type='text_field')
        self.profile_field2 = ProfileField.objects.create(key='html_key', name='html_name', field_type='html_field')
        self.profile_field3 = ProfileField.objects.create(key='select_key', name='select_name',
                                                          field_type='select_field', is_filter=True,
                                                          field_options=['select_value', 'select_value_2'])
        self.profile_field4 = ProfileField.objects.create(key='date_key', name='date_name', field_type='date_field')
        self.profile_field5 = ProfileField.objects.create(key='multi_key', is_filter=True, name='multi_name',
                                                          field_type='multi_select_field',
                                                          field_options=['select_value_1', 'select_value_2',
                                                                         'select_value_3'])
        self.profile_field6 = ProfileField.objects.create(key='multi_key2', name='multi_name2',
                                                          field_type='multi_select_field',
                                                          field_options=['select_value_1'])

        Setting.objects.create(key='PROFILE_SECTIONS', value=[
            {"name": "", "profileFieldGuids": [str(self.profile_field1.id), str(self.profile_field5.id)]},
            {"name": "section_two", "profileFieldGuids": [str(self.profile_field2.id), str(self.profile_field4.id),
                                                          str(self.profile_field6.id)]}
        ]
                               )

    def tearDown(self):
        super().tearDown()

        self.admin.delete()
        self.other.delete()
        self.user.delete()
        Setting.objects.all().delete()
        cache.clear()

    def test_query_filters_by_user(self):
        query = """
            query UsersQuery {
                filters {
                    users {
                        name
                        label
                        fieldType
                        keys
                    }
                }
            }
        """

        self.initialize_index()

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": query}, context_value={"request": request})

        data = result[1]["data"]

        self.assertEqual(data["filters"]["users"][0]["name"], "multi_key")
        self.assertEqual(data["filters"]["users"][0]["fieldType"], "multi_select_field")
        self.assertEqual(data["filters"]["users"][0]["label"], "multi_name")
        self.assertEqual(data["filters"]["users"][0]["keys"], ['select_value_1', 'select_value_2', 'select_value_3'])
        self.assertEqual(len(data["filters"]["users"]), 1)

    @staticmethod
    def _create_member_with_profile(group, profile_field, field_value):
        member = mixer.blend(User)
        profile, created = UserProfile.objects.get_or_create(user=member)
        UserProfileField.objects.get_or_create(user_profile=profile,
                                               profile_field=profile_field,
                                               value=field_value,
                                               read_access=[ACCESS_TYPE.logged_in])
        group.join(member)
        group.save()
        return member

    def test_group_filters(self):
        group = mixer.blend(Group, owner=self.user, introduction='introductionMessage')
        group.join(self.user, 'owner')
        group.save()

        self._create_member_with_profile(group, self.profile_field5, "select_value_1")
        self._create_member_with_profile(group, self.profile_field5, "select_value_2")

        GroupProfileFieldSetting.objects.create(
            profile_field=self.profile_field5,
            group=group,
            show_field=True
        )

        GroupProfileFieldSetting.objects.create(
            profile_field=self.profile_field6,
            group=group,
            show_field=True
        )

        query = """
            query UsersQuery ($groupGuid: String) {
                filters {
                    users (groupGuid: $groupGuid) {
                        name
                        label
                        fieldType
                        keys
                    }
                }
            }
        """
        variables = {
            "groupGuid": group.guid
        }

        request = HttpRequest()
        request.user = self.user

        # Elasticsearch is accessed when groups queried.
        self.initialize_index()

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        data = result[1]["data"]
        self.assertIsNotNone(data["filters"]["users"], msg=result)
        self.assertEqual(len(data["filters"]["users"]), 1)
        self.assertEqual(data["filters"]["users"][0]["name"], "multi_key")
        self.assertEqual(data["filters"]["users"][0]["fieldType"], "multi_select_field")
        self.assertEqual(data["filters"]["users"][0]["label"], "multi_name")
        self.assertEqual(data["filters"]["users"][0]["keys"], ['select_value_1', 'select_value_2'])
