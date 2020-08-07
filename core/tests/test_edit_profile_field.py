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

class EditProfileFieldTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.other = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        ProfileField.objects.create(key='text_key', name='text_name', field_type='text_field')
        ProfileField.objects.create(key='html_key', name='html_name', field_type='html_field')
        ProfileField.objects.create(key='select_key', name='select_name', field_type='select_field', field_options=['select_value', 'select_value_2'])
        ProfileField.objects.create(key='date_key', name='date_name', field_type='date_field')
        ProfileField.objects.create(key='multi_key', name='multi_name', field_type='multi_select_field',
                                    field_options=['select_value_1', 'select_value_2', 'select_value_3'])
        Setting.objects.create(key='PROFILE', value=[{"key": "text_key", "name": "text_name", "isFilter": False},
                                {"key": "html_key", "name": "html_name", "isFilter": False},
                                {"key": "select_key", "name": "select_name", "isFilter": False},
                                {"key": "date_key", "name": "date_name", "isFilter": False},
                                {"key": "multi_key", "name": "multi_name", "isFilter": False}])

    def tearDown(self):
        self.admin.delete()
        self.other.delete()
        self.user.delete()
        Setting.objects.all().delete()
        cache.clear()

    def test_edit_profile_field_by_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "text_key",
                "value": "text_value"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["key"], 'text_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["name"], 'text_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["value"], 'text_value')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["accessId"], 2)


    def test_edit_profile_field_by_admin(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "text_key",
                "value": "text_value"
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["key"], 'text_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["name"], 'text_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["value"], 'text_value')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["accessId"], 2)


    def test_edit_profile_field_by_other_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "text_key",
                "value": "text_value"
            }
        }

        request = HttpRequest()
        request.user = self.other

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")


    def test_edit_profile_field_by_anonymous(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "text_key",
                "value": "text_value"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_edit_profile_field_not_html_by_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "html_key",
                "value": "html_value"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "invalid_value")


    def test_edit_profile_select_field_not_in_options_by_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "select_key",
                "value": "select_value_fault"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "invalid_value")


    def test_edit_profile_select_field_in_options_by_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 0,
                "guid": self.user.guid,
                "key": "select_key",
                "value": "select_value_2"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })
        data = result[1]["data"]

        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["key"], 'select_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["name"], 'select_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["value"], 'select_value_2')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["accessId"], 0)

    def test_edit_profile_date_field_by_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 1,
                "guid": self.user.guid,
                "key": "date_key",
                "value": "2019-02-02"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][3]["key"], 'date_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][3]["name"], 'date_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][3]["value"], '2019-02-02')
        self.assertEqual(data["editProfileField"]["user"]["profile"][3]["accessId"], 1)


    def test_edit_profile_date_field_with_incorrect_date_by_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "date_key",
                "value": "20191-02-02"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "invalid_value")


    def test_edit_profile_multi_select_field_fields_not_in_field_options_by_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "multi_key",
                "value": "select_value_fault"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "invalid_value")


    def test_edit_profile_multi_select_field_by_user(self):

        mutation = """
            mutation editProfileField($input: editProfileFieldInput!) {
                editProfileField(input: $input) {
                    user {
                    guid
                    name
                    profile {
                        key
                        name
                        value
                        category
                        accessId
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "multi_key",
                "value": "select_value_1"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][4]["key"], 'multi_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][4]["name"], 'multi_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][4]["value"], 'select_value_1')
        self.assertEqual(data["editProfileField"]["user"]["profile"][4]["accessId"], 2)

        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "multi_key",
                "value": "select_value_1,select_value_2"
            }
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]
        self.assertEqual(data["editProfileField"]["user"]["profile"][4]["value"], 'select_value_1,select_value_2')
