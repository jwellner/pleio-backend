from core.models import ProfileFieldValidator
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class AddSiteSettingProfileFieldTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddSiteSettingProfileFieldTestCase, self).setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()

        self.profileFieldValidator1 = ProfileFieldValidator.objects.create(
            name="123",
            validator_type='inList',
            validator_data=['aap', 'noot', 'mies']
        )

    def test_add_site_setting_profile_field_by_anonymous(self):
        mutation = """
            mutation addSiteSettingProfileField($input: addSiteSettingProfileFieldInput!) {
                addSiteSettingProfileField(input: $input) {
                    profileItem {
                        key
                    }
                }
            }
        """
        variables = {
            "input": {
                "name": "new_name_1",
                "fieldType": "text_field"
            }
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(mutation, variables)

    def test_add_profile_field_by_user(self):
        mutation = """
            mutation addSiteSettingProfileField($input: addSiteSettingProfileFieldInput!) {
                addSiteSettingProfileField(input: $input) {
                    profileItem {
                        key
                    }
                }
            }
        """
        variables = {
            "input": {
                "name": "new_name_1",
                "fieldType": "text_field"
            }
        }

        with self.assertGraphQlError('user_not_site_admin'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_add_profile_field_by_admin(self):
        mutation = """
            mutation addSiteSettingProfileField($input: addSiteSettingProfileFieldInput!) {
                addSiteSettingProfileField(input: $input) {
                    profileItem {
                        key
                        name
                        category
                        isEditable
                        isFilter
                        isInOverview
                        isOnVcard
                        fieldType
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
                "name": "new_name_1",
                "isEditable": False,
                "isFilter": True,
                "isInOverview": True,
                "isOnVcard": True,
                "fieldType": "date_field",
                "fieldOptions": ["option1", "option2"],
                "isInOnboarding": True,
                "isMandatory": True,
                "profileFieldValidatorId": str(self.profileFieldValidator1.id)
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        profile_item = result["data"]["addSiteSettingProfileField"]["profileItem"]
        self.assertEqual(len(profile_item["key"]), 20)
        self.assertEqual(profile_item["name"], "new_name_1")
        self.assertEqual(profile_item["isEditable"], False)
        self.assertEqual(profile_item["isFilter"], True)
        self.assertEqual(profile_item["isInOverview"], True)
        self.assertEqual(profile_item["isOnVcard"], True)
        self.assertEqual(profile_item["fieldType"], "dateField")
        self.assertEqual(profile_item["fieldOptions"], ["option1", "option2"])
        self.assertEqual(profile_item["isInOnboarding"], True)
        self.assertEqual(profile_item["isMandatory"], True)
        self.assertEqual(profile_item["profileFieldValidator"]["name"], self.profileFieldValidator1.name)
