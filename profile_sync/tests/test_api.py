import json
import uuid

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from core.models import ProfileField, UserProfileField, Group
from mixer.backend.django import mixer

from tenants.helpers import FastTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE
from django.core.files import File
from profile_sync.models import Logs
from unittest.mock import MagicMock, patch


class ProfileSyncApiTests(FastTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User, email='user1@pleio.test')
        self.user3 = mixer.blend(User, custom_id='pl-109')
        self.user4 = mixer.blend(User, email='email@notavailable.nl', custom_id='notavailable_id')
        self.user5 = mixer.blend(User)
        self.group1 = mixer.blend(Group, owner=self.user3)

        self.profile_field1 = ProfileField.objects.create(key='occupation', name='text_name', field_type='text_field')
        self.profile_field2 = ProfileField.objects.create(key='existing', name='text_name2', field_type='text_field')

        user_profile_field = UserProfileField.objects.create(
            user_profile=self.user1.profile,
            profile_field=self.profile_field1,
            value='test_value'
        )

        self.headers = {
            'Authorization': 'Bearer 2312341234'
        }

        cache.set("%s%s" % (connection.schema_name, 'PROFILE_SYNC_ENABLED'), True)
        cache.set("%s%s" % (connection.schema_name, 'PROFILE_SYNC_TOKEN'), '2312341234')

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_get_3_users(self):
        response = self.client.get('/profile_sync_api/users?limit=3&cursor=', headers=self.headers)

        self.assertEqual(len(response.json()["users"]), 3)
        self.assertEqual(response.json()["users"][0]["name"], self.user1.name)

    def test_get_users_from_specific_id(self):
        path = '/profile_sync_api/users?limit=3&cursor=' + str(self.user3.id)
        response = self.client.get(path, headers=self.headers)

        self.assertEqual(len(response.json()["users"]), 2)
        self.assertEqual(response.json()["users"][0]["name"], self.user4.name)

    def test_get_users_with_non_existing_cursor(self):
        path = '/profile_sync_api/users?limit=3&cursor=aa'
        response = self.client.get(path, headers=self.headers)

        json_response = {
            "error": "not_found",
            "pretty_error": "Could not find user with this guid.",
            "status": 404
        }

        self.assertEqual(response.json(), json_response)

    def test_invalid_token(self):
        headers = {
            'Authorization': 'Bearer 2312341'
        }

        response = self.client.get("/profile_sync_api/users", headers=headers)

        json_response = {
            "error": "invalid_bearer_token",
            "pretty_error": "You did not supply a valid bearer token.",
            "status": 403
        }

        self.assertEqual(response.json(), json_response)

    def test_write_log(self):
        data = {
            "uuid": "asdasd78987wejkjasdljasd",
            "content": "contentcontent"
        }

        response = self.client.post('/profile_sync_api/logs', data=json.dumps(data), headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "log": {
                "uuid": "asdasd78987wejkjasdljasd"
            },
            "status": 200
        }

        self.assertEqual(response.json(), json_response)
        self.assertEqual(Logs.objects.all().count(), 1)

    def test_write_log_missing_uuid(self):
        data = {
            "content": "contentcontent"
        }

        response = self.client.post('/profile_sync_api/logs', data=json.dumps(data), headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "error": "could_not_create",
            "pretty_error": "Could not create the log entry, uuid is missing.",
            "status": 400
        }

        self.assertEqual(response.json(), json_response)

    def test_add_user(self):
        data = {
            "name": "User 7",
            "email": "user7@pleio.test",
            "external_id": "pl-107",
            "avatar": "",
            "groups": self.group1.guid,
            "profile": {
                "occupation": "Tester"
            }
        }

        response = self.client.post('/profile_sync_api/users',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "status": 200,
            "user": {}
        }

        self.assertEqual(response.json()["user"]["name"], "User 7")

        new_user = User.objects.get(email='user7@pleio.test')
        self.assertEqual(new_user.name, 'User 7')
        self.assertEqual(new_user.email, 'user7@pleio.test')
        self.assertEqual(new_user.custom_id, 'pl-107')
        self.assertEqual(new_user.memberships.all()[0].group, self.group1)

        new_field = UserProfileField.objects.filter(user_profile=new_user.profile, profile_field=self.profile_field1).first()
        self.assertEqual(new_field.value, 'Tester')

    def test_add_user_with_existing_email(self):
        data = {
            "name": "User 7",
            "email": "user1@pleio.test",
            "external_id": "pl-107",
            "avatar": "",
            "groups": self.group1.guid,
            "profile": {
                "occupation": "Tester"
            }
        }

        response = self.client.post('/profile_sync_api/users',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "error": "could_not_create",
            "pretty_error": "This e-mail is already taken by another user.",
            "status": 400
        }

        self.assertEqual(response.json(), json_response)

    def test_add_user_with_existing_external_id(self):
        data = {
            "name": "User 7",
            "email": "user1000@pleio.test",
            "external_id": "pl-109",
            "avatar": "",
            "groups": self.group1.guid,
            "profile": {
                "occupation": "Tester",
                "new_field": "newnew"
            }
        }

        response = self.client.post('/profile_sync_api/users',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "error": "could_not_create",
            "pretty_error": "This external_id is already taken by another user.",
            "status": 400
        }

        self.assertEqual(response.json(), json_response)

    def test_update_user(self):
        user_profile_field = UserProfileField.objects.create(
            user_profile=self.user5.profile,
            profile_field=self.profile_field2,
            value='test_existing',
            read_access=[ACCESS_TYPE.public]
        )

        data = {
            "guid": self.user5.guid,
            "name": "User 700",
            "email": "user700@pleio.test",
            "external_id": "pl-10700",
            "avatar": "",
            "groups": self.group1.guid,
            "profile": {
                "occupation": "Tester100",
                "existing": "update_existing"
            }
        }

        response = self.client.post('/profile_sync_api/users',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "status": 200,
            "user": {}
        }

        self.assertEqual(response.json()["user"]["name"], "User 700")

        self.user5.refresh_from_db()

        self.assertEqual(self.user5.name, 'User 700')
        self.assertEqual(self.user5.email, 'user700@pleio.test')
        self.assertEqual(self.user5.custom_id, 'pl-10700')
        self.assertEqual(self.user5.memberships.all()[0].group, self.group1)

        new_field = UserProfileField.objects.get(user_profile=self.user5.profile, profile_field=self.profile_field1)
        self.assertEqual(new_field.value, 'Tester100')
        self.assertEqual(new_field.read_access, ['user:' + self.user5.guid, 'logged_in'])

        updated_field = UserProfileField.objects.get(user_profile=self.user5.profile, profile_field=self.profile_field2)
        self.assertEqual(updated_field.value, 'update_existing')
        self.assertEqual(updated_field.read_access, ['public'])

    def test_update_user_with_non_available_email(self):
        data = {
            "guid": self.user5.guid,
            "name": "User 700",
            "email": "email@notavailable.nl",
            "external_id": "pl-10700",
            "avatar": "",
            "groups": self.group1.guid,
            "profile": {
                "occupation": "Tester100",
                "existing": "update_existing"
            }
        }

        response = self.client.post('/profile_sync_api/users',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "status": 400,
            "error": "could_not_update",
            "pretty_error": "Could not change the email to another email as the id is already taken.",
            "user": {}
        }

        self.assertEqual(response.json(), json_response)

    def test_update_user_with_non_available_external_id(self):
        data = {
            "guid": self.user5.guid,
            "name": "User 700",
            "email": "email@available.nl",
            "external_id": "notavailable_id",
            "avatar": "",
            "groups": self.group1.guid,
            "profile": {
                "occupation": "Tester100",
                "existing": "update_existing"
            }
        }

        response = self.client.post('/profile_sync_api/users',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "status": 400,
            "error": "could_not_update",
            "pretty_error": "Could not change the external_id to another external_id as the id is already taken.",
            "user": {}
        }

        self.assertEqual(response.json(), json_response)

    def test_delete_user(self):
        response = self.client.delete('/profile_sync_api/users/' + self.user2.guid,
                                      headers=self.headers,
                                      content_type="application/json")

        json_response = {
            "status": 200
        }

        self.assertEqual(response.json(), json_response)
        self.assertEqual(User.objects.filter(id=self.user2.id, is_active=True).count(), 0)

    def test_delete_non_existing_user(self):
        response = self.client.delete('/profile_sync_api/users/' + str(uuid.uuid1()),
                                      headers=self.headers,
                                      content_type="application/json")

        json_response = {
            "status": 404,
            "error": "not_found",
            "pretty_error": "Could not find user with this guid."
        }

        self.assertEqual(response.json(), json_response)

    def test_ban_user(self):
        response = self.client.post('/profile_sync_api/users/' + self.user2.guid + '/ban',
                                    headers=self.headers,
                                    content_type="application/json")

        self.user2.refresh_from_db()

        json_response = {
            "status": 200,
            "user": {
                "guid": self.user2.guid,
                "external_id": self.user2.custom_id,
                "name": self.user2.name,
                "email": self.user2.email,
                "is_member": True,
                "is_banned": not self.user2.is_active,
                "time_created": self.user2.created_at.isoformat(),
                "time_updated": self.user2.updated_at.isoformat(),
                "icontime": None,
                "profile": {'existing': '', 'occupation': ''}
            }
        }

        self.assertEqual(response.json(), json_response)
        self.assertEqual(User.objects.filter(id=self.user2.id, is_active=False, ban_reason='Verwijderd door Profile-Sync').count(), 1)

    def test_ban_non_existing_user(self):
        headers = {
            'Authorization': 'Bearer 2312341234'
        }

        response = self.client.post('/profile_sync_api/users/' + str(uuid.uuid1()) + '/ban',
                                    headers=headers,
                                    content_type="application/json")

        json_response = {
            "status": 404,
            "error": "not_found",
            "pretty_error": "Could not find user with this guid."
        }

        self.assertEqual(response.json(), json_response)

    def test_unban_user(self):
        user = mixer.blend(User, is_active=False, ban_reason='banned')

        response = self.client.post('/profile_sync_api/users/' + user.guid + '/unban',
                                    headers=self.headers,
                                    content_type="application/json")

        user.refresh_from_db()

        json_response = {
            "status": 200,
            "user": {
                "guid": user.guid,
                "external_id": user.custom_id,
                "name": user.name,
                "email": user.email,
                "is_member": True,
                "is_banned": not user.is_active,
                "time_created": user.created_at.isoformat(),
                "time_updated": user.updated_at.isoformat(),
                "icontime": None,
                "profile": {'existing': '', 'occupation': ''}
            }
        }

        self.assertEqual(response.json(), json_response)
        self.assertEqual(User.objects.filter(id=user.id, is_active=True, ban_reason='').count(), 1)

        user.delete()

    def test_unban_non_existing_user(self):
        response = self.client.post('/profile_sync_api/users/' + str(uuid.uuid1()) + '/unban',
                                    headers=self.headers,
                                    content_type="application/json")

        json_response = {
            "status": 404,
            "error": "not_found",
            "pretty_error": "Could not find user with this guid."
        }

        self.assertEqual(response.json(), json_response)

    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_change_avatar(self, mock_open):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.gif'
        file_mock.content_type = 'image/gif'

        mock_open.return_value = file_mock

        response = self.client.post('/profile_sync_api/users/' + self.user3.guid + '/avatar',
                                    headers=self.headers,
                                    data={'avatar': file_mock},
                                    format='multipart')

        self.user3.refresh_from_db()

        json_response = {
            "status": 200,
            "user": {
                "guid": self.user3.guid,
                "external_id": self.user3.custom_id,
                "name": self.user3.name,
                "email": self.user3.email,
                "is_member": True,
                "is_banned": not self.user3.is_active,
                "time_created": self.user3.created_at.isoformat(),
                "time_updated": self.user3.updated_at.isoformat(),
                "icontime": None,
                "profile": {'existing': '', 'occupation': ''}
            }
        }

        self.assertEqual(response.json(), json_response)
        self.assertIn('test.gif', self.user3.profile.picture_file.upload.name)

    def test_change_avatar_non_existing_user(self):
        response = self.client.post('/profile_sync_api/users/' + str(uuid.uuid1()) + '/avatar',
                                    headers=self.headers,
                                    content_type="application/json"
                                    )

        json_response = {
            "status": 404,
            "error": "not_found",
            "pretty_error": "Could not find user with this guid."
        }

        self.assertEqual(response.json(), json_response)
