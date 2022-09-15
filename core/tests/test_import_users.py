from django.db import connection
from core.lib import get_tmp_file_path, access_id_to_acl
from core.tasks import import_users
from django.contrib.auth.models import AnonymousUser
from core.models import ProfileField, UserProfileField
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from django.core.cache import cache


class ImportUsersTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        cache.set("%s%s" % (connection.schema_name, 'IS_CLOSED'), False)  # or we can not test access id 2

        self.csv_bytes = (
            b'column1;column2;column3;column4;column5\n'
            b'row-1-1;row-1-2@example.com;row-1-3;row-1-4;row-1-5\n'
            b'row-2-1;row-2-2@example.com;row-2-3;row-2-4;row-2-5\n'
            b'row-3-1;row-3-2@example.com;row-3-3;row-3-4;row-3-5'
        )
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User, name="user_name")
        self.existing_user = mixer.blend(User, name="existing_user", email="row-2-2@example.com")

        self.admin = mixer.blend(User, roles=['ADMIN'], name="admin_name")
        self.profileField1 = mixer.blend(ProfileField)
        self.profileField2 = mixer.blend(ProfileField)

        self.existing_user_profile_field2 = UserProfileField.objects.create(
            profile_field=self.profileField2,
            user_profile=self.existing_user.profile,
            value="test",
            read_access=access_id_to_acl(self.existing_user, 2)
        )

        self.upload = SimpleUploadedFile('test.csv', self.csv_bytes)
        self.usersCsv = get_tmp_file_path(self.admin, ".csv")

        with open(self.usersCsv, 'wb+') as destination:
            for chunk in SimpleUploadedFile('test.csv', self.csv_bytes).chunks():
                destination.write(chunk)

    def teardown(self):
        super().tearDown()

        os.remove(self.usersCsv)
        User.objects.all().delete()

    def test_import_users_step1_admin(self):
        mutation = """
            mutation ($input: importUsersStep1Input!) {
                importUsersStep1(input: $input) {
                    importId
                    csvColumns
                    userFields {
                        value
                        label
                    }
                    accessIdOptions {
                        value
                        label
                    }
                }
            }
        """

        variables = {
            "input": {
                "usersCsv": self.upload
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]["importUsersStep1"]

        self.assertEqual(data["csvColumns"], ["column1", "column2", "column3", 'column4', 'column5'])
        self.assertEqual(data["userFields"][3]["label"], self.profileField1.name)

    @patch('core.resolvers.mutation_import_users.import_users.delay')
    def test_import_users_step2_admin_new_users(self, mocked_import_users):
        mutation = """
            mutation ($input: importUsersStep2Input!) {
                importUsersStep2(input: $input) {
                    success
                }
            }
        """

        fields = [
            {"csvColumn": "column2", "userField": 'email'},
            {"csvColumn": "column3", "userField": 'name'},
            {"csvColumn": "column4", "userField": str(self.profileField1.id), "accessId": 2},
            {"csvColumn": "column5", "userField": str(self.profileField2.id), "accessId": 0, "forceAccess": True}
        ]

        variables = {
            "input": {
                "importId": os.path.basename(self.usersCsv),
                "fields": fields
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(mutation, variables)
        data = result["data"]["importUsersStep2"]

        self.assertEqual(data["success"], True)

        # call import task synchronous
        import_users.s(connection.schema_name, fields, self.usersCsv, self.admin.guid).apply()

        new_users = User.objects.all().exclude(name__in=['user_name', 'admin_name', 'existing_user']).count()
        self.assertEqual(new_users, 2)

        user1 = User.objects.get(email='row-1-2@example.com')
        user1_profile_field1 = UserProfileField.objects.get(profile_field=self.profileField1, user_profile=user1.profile)
        self.assertEqual(user1_profile_field1.value, 'row-1-4')
        self.assertEqual(user1_profile_field1.read_access, ['user:' + str(user1.id), 'public'])

        self.existing_user.refresh_from_db()
        self.existing_user_profile_field2.refresh_from_db()

        self.assertEqual(self.existing_user_profile_field2.value, 'row-2-5')
        self.assertEqual(self.existing_user_profile_field2.read_access, ['user:' + self.existing_user.guid])

    def test_import_users_step2_admin_invalid_user_field(self):
        mutation = """
            mutation ($input: importUsersStep2Input!) {
                importUsersStep2(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "importId": os.path.basename(self.usersCsv),
                "fields": [
                    {"csvColumn": "column2", "userField": str(self.profileField1.id), "accessId": 0, "forceAccess": False},
                    {"csvColumn": "column3", "userField": "wrongField", "accessId": 2, "forceAccess": True}
                ]
            }
        }

        with self.assertGraphQlError("invalid_user_field"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(mutation, variables)

    def test_import_users_step2_admin_invalid_access_id(self):
        mutation = """
            mutation ($input: importUsersStep2Input!) {
                importUsersStep2(input: $input) {
                    success
                }
            }
        """
        variables = {
            "input": {
                "importId": os.path.basename(self.usersCsv),
                "fields": [
                    {"csvColumn": "column2", "userField": str(self.profileField1.id), "accessId": 0, "forceAccess": False},
                    {"csvColumn": "column3", "userField": str(self.profileField1.id), "accessId": 100, "forceAccess": True}
                ]
            }
        }

        with self.assertGraphQlError("invalid_access_id"):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(mutation, variables)

    @patch('core.tasks.misc.schedule_user_import_success')
    def test_import_user_step2_success_mail(self, mocked_send_mail_multi):
        fields = [
            {"csvColumn": "column2", "userField": 'email'},
            {"csvColumn": "column3", "userField": 'name'},
            {"csvColumn": "column4", "userField": str(self.profileField1.id), "accessId": 2},
            {"csvColumn": "column5", "userField": str(self.profileField2.id), "accessId": 0, "forceAccess": True}
        ]

        import_users.s(connection.schema_name, fields, self.usersCsv, self.admin.guid).apply()

        self.assertEqual(mocked_send_mail_multi.call_count, 1)

    @patch('core.tasks.misc.schedule_user_import_failed')
    def test_import_user_step2_error_mail(self, mocked_send_mail_multi):
        fields = [
            {"csvColumn": "column2", "userField": 'email'},
            {"csvColumn": "column3", "userField": 'name'},
            {"csvColumn": "column4", "userField": str(self.profileField1.id), "accessId": 2},
            {"csvColumn": "column5", "userField": str(self.profileField2.id), "accessId": 0, "forceAccess": True}
        ]

        import_users.s(connection.schema_name, fields, '/tmp/does/not/exist.csv', self.admin.guid).apply()

        self.assertEqual(mocked_send_mail_multi.call_count, 1)
