from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from django.core.files.uploadedfile import SimpleUploadedFile


class AddSiteSettingProfileFieldValidatorTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddSiteSettingProfileFieldValidatorTestCase, self).setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()

    def test_add_site_setting_profile_field_by_anonymous(self):
        mutation = """
            mutation addSiteSettingProfileFieldValidator($input: addSiteSettingProfileFieldValidatorInput!) {
                addSiteSettingProfileFieldValidator(input: $input) {
                    profileFieldValidator {
                        id
                        type
                    }
                }
            }
        """
        variables = {
            "input": {
                "type": "inList",
                "name": "lala"
            }
        }

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(mutation, variables)


    def test_add_profile_field_by_user(self):
        mutation = """
            mutation addSiteSettingProfileFieldValidator($input: addSiteSettingProfileFieldValidatorInput!) {
                addSiteSettingProfileFieldValidator(input: $input) {
                    profileFieldValidator {
                        id
                        type
                    }
                }
            }
        """
        variables = {
            "input": {
                "type": "inList",
                "name": "lala"
            }
        }

        with self.assertGraphQlError('user_not_site_admin'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_add_profile_field_by_admin(self):
        mutation = """
            mutation addSiteSettingProfileFieldValidator($input: addSiteSettingProfileFieldValidatorInput!) {
                addSiteSettingProfileFieldValidator(input: $input) {
                    profileFieldValidator {
                        id
                        type
                        name
                        validationList
                        validationString
                    }
                }
            }
        """

        csv_bytes = (
            b'aap;row-1-2@example.com;row-1-3;row-1-4;row-1-5\n'
            b'noot;row-2-2@example.com;row-2-3;row-2-4;row-2-5\n'
            b'mies;row-3-2@example.com;row-3-3;row-3-4;row-3-5'
        )

        upload = SimpleUploadedFile('test.csv', csv_bytes)

        variables = {
            "input": {
                "type": "inList",
                "name": "Naampje",
                "validationListFile": upload
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        profile_field_validator = result["data"]["addSiteSettingProfileFieldValidator"]["profileFieldValidator"]
        self.assertEqual(profile_field_validator["name"], "Naampje")
        self.assertEqual(profile_field_validator["type"], "inList")
        self.assertEqual(profile_field_validator["validationList"], ["aap", "noot", "mies"])
        self.assertEqual(profile_field_validator["validationString"], None)

