from core.models import ProfileField, ProfileFieldValidator
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class DeleteSiteSettingProfileFieldValidatorTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.profileFieldValidator1 = ProfileFieldValidator.objects.create(name='beconnummer', validator_type='inList', validator_data=['123', '452'])
        self.profileFieldValidator2 = ProfileFieldValidator.objects.create(name='geheim', validator_type='inList', validator_data=['wachtwoord'])

        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField1.validators.add(self.profileFieldValidator1)
        self.profileField1.validators.add(self.profileFieldValidator2)

    def tearDown(self):
        super().tearDown()

    def test_delete_site_setting_profile_field_validator_by_anonymous(self):
        mutation = """
            mutation deleteSiteSettingProfileFieldValidator($input: deleteSiteSettingProfileFieldValidatorInput!) {
                deleteSiteSettingProfileFieldValidator(input: $input) {
                    success
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

    def test_delete_profile_field_validator_by_user(self):
        mutation = """
            mutation deleteSiteSettingProfileFieldValidator($input: deleteSiteSettingProfileFieldValidatorInput!) {
                deleteSiteSettingProfileFieldValidator(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "id": str(self.profileFieldValidator1.id)
            }
        }

        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.user1)
            self.graphql_client.post(mutation, variables)

    def test_delete_site_setting_profile_field_validator_by_admin(self):
        mutation = """
            mutation deleteSiteSettingProfileFieldValidator($input: deleteSiteSettingProfileFieldValidatorInput!) {
                deleteSiteSettingProfileFieldValidator(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "id": str(self.profileFieldValidator1.id)
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["deleteSiteSettingProfileFieldValidator"]["success"], True)
        self.assertEqual(ProfileFieldValidator.objects.all().count(), 1)
        self.assertEqual(self.profileField1.validators.all().count(), 1)
