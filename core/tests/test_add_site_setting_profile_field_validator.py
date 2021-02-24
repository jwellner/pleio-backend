from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.core.cache import cache
from core.lib import is_valid_json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, ProfileField, Setting
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from django.core.files.uploadedfile import SimpleUploadedFile


class AddSiteSettingProfileFieldValidatorTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])

    def tearDown(self):
        self.admin.delete()
        self.user.delete()
        cache.clear()


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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


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

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "user_not_site_admin")


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

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addSiteSettingProfileFieldValidator"]["profileFieldValidator"]["type"], "inList")
        self.assertEqual(data["addSiteSettingProfileFieldValidator"]["profileFieldValidator"]["name"], "Naampje")
        self.assertEqual(data["addSiteSettingProfileFieldValidator"]["profileFieldValidator"]["validationList"], ["aap", "noot", "mies"])
        self.assertEqual(data["addSiteSettingProfileFieldValidator"]["profileFieldValidator"]["validationString"], None)

