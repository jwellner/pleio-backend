from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from core.lib import is_valid_json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, ProfileFieldValidator, Setting
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from django.core.files.uploadedfile import SimpleUploadedFile

class EditSiteSettingProfileFieldValidatorTestCase(FastTenantTestCase):

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
        self.profileFieldValidator1.delete()
        self.user.delete()

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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


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

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")


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

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editSiteSettingProfileFieldValidator"]["profileFieldValidator"]["type"], "inList")
        self.assertEqual(data["editSiteSettingProfileFieldValidator"]["profileFieldValidator"]["name"], "Nieuwe naam")
        self.assertEqual(data["editSiteSettingProfileFieldValidator"]["profileFieldValidator"]["validationList"], ["raap", "bep", "maas"])
        self.assertEqual(data["editSiteSettingProfileFieldValidator"]["profileFieldValidator"]["validationString"], None)
