from django.db import connection
from django.core.cache import cache
from core.models import ProfileField, UserProfileField, Setting
from core.tests.helpers import PleioTenantTestCase, override_config
from user.models import User
from mixer.backend.django import mixer


class DeleteSiteSettingProfileFieldTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name', field_type='text_field')
        self.userProfileField1 = mixer.blend(UserProfileField, profile_field=self.profileField1, user_profile=self.user1.profile)
        self.userProfileField2 = mixer.blend(UserProfileField, profile_field=self.profileField1, user_profile=self.user2.profile)
        self.userProfileField3 = mixer.blend(UserProfileField, profile_field=self.profileField2, user_profile=self.user2.profile)

        self.profile_section_setting, _ = Setting.objects.get_or_create(key='PROFILE_SECTIONS')
        self.profile_section_setting.value = [
            {"name": "section_one", "profileFieldGuids": [str(self.profileField1.id)]},
            {"name": "section_two", "profileFieldGuids": [str(self.profileField2.id)]}
        ]
        self.profile_section_setting.save()

    def tearDown(self):
        super().tearDown()

    def test_delete_site_setting_profile_field_by_anonymous(self):
        mutation = """
            mutation deleteSiteSettingProfileField($input: deleteSiteSettingProfileFieldInput!) {
                deleteSiteSettingProfileField(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": str(self.profileField1.id)
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_delete_profile_field_by_user(self):
        mutation = """
            mutation deleteSiteSettingProfileField($input: deleteSiteSettingProfileFieldInput!) {
                deleteSiteSettingProfileField(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": str(self.profileField1.id)
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(mutation, variables)

    def test_delete_site_setting_profile_field_by_admin(self):
        mutation = """
            mutation deleteSiteSettingProfileField($input: deleteSiteSettingProfileFieldInput!) {
                deleteSiteSettingProfileField(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "guid": str(self.profileField1.id)
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["deleteSiteSettingProfileField"]["success"], True)
        self.assertEqual(ProfileField.objects.all().count(), 1)
        self.assertEqual(UserProfileField.objects.all().count(), 1)

    def test_profile_sections_after_delete_by_admin(self):
        mutation = """
            mutation deleteSiteSettingProfileField($input: deleteSiteSettingProfileFieldInput!) {
                deleteSiteSettingProfileField(input: $input) {
                    success
                }
            }
        """

        query = """
            query SiteGeneralSettings {
                siteSettings {
                    profileSections {
                        name
                        profileFieldGuids
                    }
                }
            }
        """

        variables = {
            "input": {
                "guid": str(self.profileField1.id)
            }
        }

        self.graphql_client.force_login(self.admin)
        self.graphql_client.post(mutation, variables)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["siteSettings"]["profileSections"], [{"name": "section_one", "profileFieldGuids": []},
                                                                   {"name": "section_two", "profileFieldGuids": [str(self.profileField2.id)]}])
