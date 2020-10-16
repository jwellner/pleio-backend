from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.core.cache import cache
from core.lib import is_valid_json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, ProfileField, Setting, UserProfileField
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError

class DeleteSiteSettingProfileFieldTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField2 = ProfileField.objects.create(key='text_key2', name='text_name', field_type='text_field')
        self.userProfileField1 = mixer.blend(UserProfileField, profile_field=self.profileField1, user_profile=self.user1.profile)
        self.userProfileField2 = mixer.blend(UserProfileField, profile_field=self.profileField1, user_profile=self.user2.profile)
        self.userProfileField3 = mixer.blend(UserProfileField, profile_field=self.profileField2, user_profile=self.user2.profile)

    def tearDown(self):
        self.admin.delete()
        self.profileField1.delete()
        self.profileField2.delete()
        self.user1.delete()
        self.user2.delete()
        cache.clear()


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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


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
        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")


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

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        data = result[1]["data"]

        self.assertEqual(data["deleteSiteSettingProfileField"]["success"], True)
        self.assertEqual(ProfileField.objects.all().count(), 1)
        self.assertEqual(UserProfileField.objects.all().count(), 1)
