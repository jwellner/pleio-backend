from django.core.cache import cache
from mixer.backend.django import mixer

from core.models import ProfileField, ProfileFieldValidator
from core.tests.helpers import PleioTenantTestCase
from user.models import User


class EditSiteSettingProfileFieldTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.profileField1 = ProfileField.objects.create(key='text_key', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name2', field_type='text_field')

        self.profileFieldValidator1 = ProfileFieldValidator.objects.create(
            name="123",
            validator_type='inList',
            validator_data=['aap', 'noot', 'mies']
        )

    def tearDown(self):
        self.admin.delete()
        self.profileField1.delete()
        self.user.delete()
        cache.clear()
        super().tearDown()

    def test_edit_site_setting_profile_field_by_anonymous(self):
        mutation = """
            mutation editSiteSettingProfileField($input: editSiteSettingProfileFieldInput!) {
                editSiteSettingProfileField(input: $input) {
                    profileItem {
                        guid
                    }
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

    def test_edit_profile_field_by_user(self):
        mutation = """
            mutation editSiteSettingProfileField($input: editSiteSettingProfileFieldInput!) {
                editSiteSettingProfileField(input: $input) {
                    profileItem {
                        guid
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": str(self.profileField1.id)
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_edit_profile_field_by_admin(self):
        mutation = """
            mutation editSiteSettingProfileField($input: editSiteSettingProfileFieldInput!) {
                editSiteSettingProfileField(input: $input) {
                    profileItem {
                        guid
                        name
                        key
                        category
                        isEditable
                        isFilter
                        isInOverview
                        isOnVcard
                        fieldOptions
                        isInOnboarding
                        isMandatory
                        profileFieldValidator {
                            name
                        }
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": str(self.profileField1.id),
                "name": "new_name_1",
                "key": "readable_key",
                "isEditable": False,
                "isFilter": True,
                "isInOverview": True,
                "isOnVcard": True,
                "fieldOptions": ["option1", "option2"],
                "isInOnboarding": True,
                "isMandatory": True,
                "profileFieldValidatorId": str(self.profileFieldValidator1.id)
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["guid"], str(self.profileField1.id))
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["name"], "new_name_1")
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["key"], "readable_key")
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["isEditable"], False)
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["isFilter"], True)
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["isInOverview"], True)
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["isOnVcard"], True)
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["fieldOptions"], ["option1", "option2"])
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["isInOnboarding"], True)
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["isMandatory"], True)
        self.assertEqual(data["editSiteSettingProfileField"]["profileItem"]["profileFieldValidator"]["name"], self.profileFieldValidator1.name)

    def test_edit_profile_field_existing_key(self):
        mutation = """
            mutation editSiteSettingProfileField($input: editSiteSettingProfileFieldInput!) {
                editSiteSettingProfileField(input: $input) {
                    profileItem {
                        key

                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": str(self.profileField2.id),
                "key": "text_key"
            }
        }

        with self.assertGraphQlError("key_already_in_use"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(mutation, variables)
