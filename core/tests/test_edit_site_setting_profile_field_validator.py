from core.models import ProfileFieldValidator
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from django.core.files.uploadedfile import SimpleUploadedFile


class EditSiteSettingProfileFieldValidatorTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.profileFieldValidator1 = ProfileFieldValidator.objects.create(
            name="123",
            validator_type='inList',
            validator_data=['aap', 'noot', 'mies']
        )

    def tearDown(self):
        super().tearDown()

    def test_edit_site_setting_profile_field_by_anonymous(self):
        mutation = """
            mutation editSiteSettingProfileFieldValidator($input: editSiteSettingProfileFieldValidatorInput!) {
                editSiteSettingProfileFieldValidator(input: $input) {
                    profileFieldValidator {
                        id
                    }
                }
            }
        """
        variables = {
            "input": {
                "id": str(self.profileFieldValidator1.id)
            }
        }

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

    def test_edit_profile_field_by_user(self):
        mutation = """
            mutation editSiteSettingProfileFieldValidator($input: editSiteSettingProfileFieldValidatorInput!) {
                editSiteSettingProfileFieldValidator(input: $input) {
                    profileFieldValidator {
                        id
                    }
                }
            }
        """
        variables = {
            "input": {
                "id": str(self.profileFieldValidator1.id)
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_edit_profile_field_by_admin(self):
        mutation = """
            mutation editSiteSettingProfileFieldValidator($input: editSiteSettingProfileFieldValidatorInput!) {
                editSiteSettingProfileFieldValidator(input: $input) {
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
            b'raap;row-1-2@example.com;row-1-3;row-1-4;row-1-5\n'
            b'bep;row-2-2@example.com;row-2-3;row-2-4;row-2-5\n'
            b'maas;row-3-2@example.com;row-3-3;row-3-4;row-3-5\n'
            b';'
        )

        upload = SimpleUploadedFile('test.csv', csv_bytes)

        variables = {
            "input": {
                "id": str(self.profileFieldValidator1.id),
                "validationListFile": upload,
                "name": "Nieuwe naam"
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editSiteSettingProfileFieldValidator"]["profileFieldValidator"]["type"], "inList")
        self.assertEqual(data["editSiteSettingProfileFieldValidator"]["profileFieldValidator"]["name"], "Nieuwe naam")
        self.assertEqual(data["editSiteSettingProfileFieldValidator"]["profileFieldValidator"]["validationList"], ["raap", "bep", "maas"])
        self.assertEqual(data["editSiteSettingProfileFieldValidator"]["profileFieldValidator"]["validationString"], None)
