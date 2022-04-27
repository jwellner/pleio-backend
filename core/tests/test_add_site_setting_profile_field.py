from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.core.cache import cache
from core.lib import is_valid_json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, ProfileField, Setting, ProfileFieldValidator, ProfileFieldValidator
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError

class AddSiteSettingProfileFieldTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])

        self.profileFieldValidator1 = ProfileFieldValidator.objects.create(
            name="123",
            validator_type='inList',
            validator_data=['aap', 'noot', 'mies']
        )


    def tearDown(self):
        self.admin.delete()
        self.user.delete()
        cache.clear()


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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


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
        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")


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
        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(len(data["addSiteSettingProfileField"]["profileItem"]["key"]), 20)
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["name"], "new_name_1")
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["isEditable"], False)
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["isFilter"], True)
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["isInOverview"], True)
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["isOnVcard"], True)
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["fieldType"], "dateField")
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["fieldOptions"], ["option1", "option2"])
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["isInOnboarding"], True)
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["isMandatory"], True)
        self.assertEqual(data["addSiteSettingProfileField"]["profileItem"]["profileFieldValidator"]["name"], self.profileFieldValidator1.name)
