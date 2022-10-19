from django.core.cache import cache
from core.models import ProfileField, Setting, ProfileFieldValidator
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class EditProfileFieldTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.other = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()

        self.profile_field_validator = ProfileFieldValidator.objects.create(validator_type='inList', validator_data=['aap', 'noot', 'mies', 'text_value'])

        self.profile_field1 = ProfileField.objects.create(key='text_key', name='text_name', field_type='text_field')
        self.profile_field1.validators.add(self.profile_field_validator)
        self.profile_field1.save()

        self.profile_field2 = ProfileField.objects.create(key='html_key', name='html_name', field_type='html_field')
        self.profile_field3 = ProfileField.objects.create(key='select_key', name='select_name', field_type='select_field',
                                                          field_options=['select_value', 'select_value_2'])
        self.profile_field4 = ProfileField.objects.create(key='date_key', name='date_name', field_type='date_field')
        self.profile_field5 = ProfileField.objects.create(key='multi_key', name='multi_name', field_type='multi_select_field',
                                                          field_options=['select_value_1', 'select_value_2', 'select_value_3'])
        Setting.objects.create(key='PROFILE_SECTIONS', value=[{
            "name": "",
            "profileFieldGuids": [
                str(self.profile_field1.id), str(self.profile_field2.id), str(self.profile_field3.id),
                str(self.profile_field4.id), str(self.profile_field5.id)
            ]
        }])

    def tearDown(self):
        self.admin.delete()
        self.other.delete()
        self.user.delete()
        Setting.objects.all().delete()
        cache.clear()
        super().tearDown()

    def test_edit_profile_field_by_user(self):
        mutation = """
            mutation leditProfileField($input: editProfileFieldInput!) {
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

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.other)
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("invalid_value"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_edit_profile_field_invalid_html_field_by_user(self):
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
                "value": '{"type":"doc","content":[{"type":"file","attrs":{"name":"panic.jpeg","mimeType":"image/jpeg","url":"http://somesite.com/scam.exe","size":78256}}]}'
            }
        }

        with self.assertGraphQlError("invalid_value"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_edit_profile_field_valid_html_field_by_user(self):
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
                "value": '{"type":"doc","content":[{"type":"file","attrs":{"name":"panic.jpeg","mimeType":"image/jpeg","url":"/valid_url","size":78256}}]}'
            }
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][1]["key"], 'html_key')

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

        with self.assertGraphQlError("invalid_value"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_edit_profile_select_field_empty_by_user(self):
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
                "value": ""
            }
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["key"], 'select_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["name"], 'select_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["value"], '')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["accessId"], 2)

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

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["key"], 'select_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["name"], 'select_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["value"], 'select_value_2')
        self.assertEqual(data["editProfileField"]["user"]["profile"][2]["accessId"], 0)

    def test_edit_profile_date_field_empty_by_user(self):
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
                "value": ""
            }
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][3]["key"], 'date_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][3]["name"], 'date_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][3]["value"], '')
        self.assertEqual(data["editProfileField"]["user"]["profile"][3]["accessId"], 1)

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

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        with self.assertGraphQlError("invalid_value"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

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

        with self.assertGraphQlError("invalid_value"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)

    def test_edit_profile_multi_select_field_fields_empty_by_user(self):
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
                "value": ""
            }
        }

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editProfileField"]["user"]["profile"][4]["value"], "")

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

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
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

        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editProfileField"]["user"]["profile"][4]["value"], 'select_value_1,select_value_2')

    def test_edit_profile_field_with_validator_by_user(self):
        mutation = """
            mutation leditProfileField($input: editProfileFieldInput!) {
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
                "value": "boom"
            }
        }

        with self.assertGraphQlError("invalid_value"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(mutation, variables)


        variables = {
            "input": {
                "accessId": 2,
                "guid": self.user.guid,
                "key": "text_key",
                "value": "aap"
            }
        }

        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editProfileField"]["user"]["guid"], self.user.guid)
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["key"], 'text_key')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["name"], 'text_name')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["value"], 'aap')
        self.assertEqual(data["editProfileField"]["user"]["profile"][0]["accessId"], 2)
