from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.core.cache import cache
from core import config
from core.lib import is_valid_json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, ProfileField, Setting, UserProfileField, ProfileFieldValidator
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError

class DeleteSiteSettingProfileFieldValidatorTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.profileFieldValidator1 = ProfileFieldValidator.objects.create(name='beconnummer', validator_type='inList', validator_data=['123', '452'])
        self.profileFieldValidator2 = ProfileFieldValidator.objects.create(name='geheim', validator_type='inList', validator_data=['wachtwoord'])

        self.profileField1 = ProfileField.objects.create(key='text_key1', name='text_name', field_type='text_field')
        self.profileField1.validators.add(self.profileFieldValidator1)
        self.profileField1.validators.add(self.profileFieldValidator2)

    def tearDown(self):
        self.admin.delete()
        self.profileFieldValidator1.delete()
        self.profileFieldValidator2.delete()
        self.user1.delete()


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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


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

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")


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

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        data = result[1]["data"]

        self.assertEqual(data["deleteSiteSettingProfileFieldValidator"]["success"], True)
        self.assertEqual(ProfileFieldValidator.objects.all().count(), 1)
        self.assertEqual(self.profileField1.validators.all().count(), 1)

