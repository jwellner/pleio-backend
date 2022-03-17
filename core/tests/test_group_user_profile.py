from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django_tenants.test.cases import FastTenantTestCase

from backend2.schema import schema
from core.models import Group, ProfileField, GroupProfileFieldSetting, UserProfile, UserProfileField
from user.models import User
from mixer.backend.django import mixer


class UserSettingsTestCase(FastTenantTestCase):

    def setUp(self):
        self.member = mixer.blend(User)
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
            query ($guid: String!) {
                memberProfileModal(groupGuid: $guid) {
                    total
                    edges {
                        guid
                    }
                    intro
                }
            }
        """
        self.variables = {
            "guid": self.group.guid
        }

    def graphql_sync(self, visitor, expect_errors=False):
        request = HttpRequest()
        request.user = visitor

        success, result = graphql_sync(schema, {"query": self.query, "variables": self.variables},
                                       context_value={"request": request})

        self.assertTrue(success, msg=result)
        if not expect_errors:
            self.assertIsNone(result.get('errors'), msg=result.get('errors'))

        return result.get('data')

    def test_query_should_give_profile_field_info_when_user_has_profile_not_filled_in(self):
        data = self.graphql_sync(visitor=self.member)

        self.assertEqual(data['memberProfileModal']['total'], 1)
        self.assertEqual(data['memberProfileModal']['intro'], self.group.required_fields_message)
        self.assertEqual(data['memberProfileModal']['edges'][0]['guid'], self.profile_field.guid)

    def test_query_should_not_give_profile_field_info_when_user_has_profile_filled_in(self):
        user_profile, created = UserProfile.objects.get_or_create(user=self.member)
        UserProfileField.objects.create(
            user_profile=user_profile,
            profile_field=self.profile_field,
            value="some value"
        )

        data = self.graphql_sync(visitor=self.member)

        self.assertEqual(data['memberProfileModal']['total'], 0)

    def test_query_should_not_give_profile_field_info_in_case_of_an_anonymous_user(self):
        data = self.graphql_sync(visitor=AnonymousUser())

        self.assertEqual(data['memberProfileModal']['total'], 0)
