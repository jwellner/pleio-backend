from core.constances import ACCESS_TYPE
from core.models import Group, ProfileField, GroupProfileFieldSetting, UserProfile, UserProfileField
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class UserProfileModalTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.member = mixer.blend(User, name="Member")
        self.group = mixer.blend(Group, required_fields_message="Please complete your profile")
        self.profile_field = ProfileField.objects.create(
            key='text_key',
            name='text_name',
            field_type='text_field'
        )
        GroupProfileFieldSetting.objects.create(
            group=self.group,
            profile_field=self.profile_field,
            is_required=True
        )

        self.query = """
            query ($user: String!, $group: String!) {
                entity(guid: $user) {
                    guid
                    ... on User {
                        missingProfileFields(groupGuid: $group) {
                        ... on ProfileItem {
                                guid
                                accessId
                            }
                        }
                    }
                }
            }
        """
        self.variables = {
            "group": self.group.guid,
            "user": self.member.guid
        }

    def assertProfileFieldsMissing(self, data):
        self.assertEqual(len(data['entity']['missingProfileFields']), 1)
        self.assertEqual(data['entity']['missingProfileFields'][0]['guid'], self.profile_field.guid)

    def assertProfileFieldsOK(self, data):
        self.assertEqual(len(data['entity']['missingProfileFields']), 0)

    def test_query_should_give_profile_field_info_when_user_has_profile_not_filled_in(self):
        self.graphql_client.force_login(self.member)
        result = self.graphql_client.post(self.query, self.variables)

        self.assertProfileFieldsMissing(result['data'])

    def test_query_should_not_give_profile_field_info_when_user_has_profile_filled_in(self):
        user_profile, created = UserProfile.objects.get_or_create(user=self.member)
        UserProfileField.objects.create(
            user_profile=user_profile,
            profile_field=self.profile_field,
            value="some value"
        )

        self.graphql_client.force_login(self.member)
        result = self.graphql_client.post(self.query, self.variables)

        self.assertProfileFieldsOK(result['data'])

    def test_query_should_give_profile_field_info_when_user_has_empty_string_profile(self):
        user_profile, created = UserProfile.objects.get_or_create(user=self.member)
        UserProfileField.objects.create(
            user_profile=user_profile,
            profile_field=self.profile_field,
            value=''
        )

        self.graphql_client.force_login(self.member)
        result = self.graphql_client.post(self.query, self.variables)

        self.assertProfileFieldsMissing(result['data'])

    def test_query_should_copy_access_properties_in_profile_items(self):
        user_profile, created = UserProfile.objects.get_or_create(user=self.member)
        UserProfileField.objects.create(
            user_profile=user_profile,
            profile_field=self.profile_field,
            read_access=[ACCESS_TYPE.logged_in],
            value='',
        )

        self.graphql_client.force_login(self.member)
        result = self.graphql_client.post(self.query, self.variables)

        self.assertEqual(result['data']['entity']['missingProfileFields'][0]['accessId'], 1)
