from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.files import File
from django.core.cache import cache
from django.http import HttpRequest
from core.constances import USER_ROLES
from core.models import Group, ProfileField
from user.models import User
from mixer.backend.django import mixer
from unittest.mock import patch, MagicMock


class EditGroupCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.group = mixer.blend(Group, owner=self.user)

    def tearDown(self):
        cache.clear()

    def test_edit_group_anon(self):
        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        name
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid,
                "name": "test"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_edit_group(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'icon.png'
        file_mock.content_type = 'image/png'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        guid
                        name
                        icon
                        excerpt
                        richDescription
                        introduction
                        isIntroductionPublic
                        welcomeMessage
                        isClosed
                        isHidden
                        isMembershipOnRequest
                        isFeatured
                        isSubmitUpdatesEnabled
                        autoNotification
                        tags
                        isLeavingGroupDisabled
                        isAutoMembershipEnabled
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid,
                "name": "Name",
                "icon": "icon.png",
                "richDescription": "<p>richDescription</p>",
                "introduction": "introdcution",
                "isIntroductionPublic": True,
                "welcomeMessage": "welcomeMessage",
                "isClosed": True,
                "isMembershipOnRequest": True,
                "isFeatured": True,
                "isSubmitUpdatesEnabled": False,
                "autoNotification": True,
                "tags": ["tag_one", "tag_two"],
                "isLeavingGroupDisabled": True,
                "isAutoMembershipEnabled": True,
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        data = result[1]["data"]

        self.assertEqual(data["editGroup"]["group"]["guid"], variables["group"]["guid"])
        self.assertEqual(data["editGroup"]["group"]["name"], variables["group"]["name"])
        self.assertIn('/icon.png', data["editGroup"]["group"]["icon"])
        self.assertEqual(data["editGroup"]["group"]["richDescription"], variables["group"]["richDescription"])
        self.assertEqual(data["editGroup"]["group"]["introduction"], variables["group"]["introduction"])
        self.assertEqual(data["editGroup"]["group"]["isIntroductionPublic"], variables["group"]["isIntroductionPublic"])
        self.assertEqual(data["editGroup"]["group"]["welcomeMessage"], variables["group"]["welcomeMessage"])
        self.assertEqual(data["editGroup"]["group"]["isClosed"], variables["group"]["isClosed"])
        self.assertEqual(data["editGroup"]["group"]["isMembershipOnRequest"], variables["group"]["isMembershipOnRequest"])
        self.assertEqual(data["editGroup"]["group"]["isFeatured"], False)
        self.assertEqual(data["editGroup"]["group"]["isLeavingGroupDisabled"], False)
        self.assertEqual(data["editGroup"]["group"]["isAutoMembershipEnabled"], False)
        self.assertEqual(data["editGroup"]["group"]["isSubmitUpdatesEnabled"], False)
        self.assertEqual(data["editGroup"]["group"]["autoNotification"], variables["group"]["autoNotification"])
        self.assertEqual(data["editGroup"]["group"]["tags"], ["tag_one", "tag_two"])

    def test_edit_group_member_fields_invalid_id(self):
        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        guid
                        showMemberProfileFields {
                            guid
                            name
                        }
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid,
                "showMemberProfileFieldGuids": ['123']
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "invalid_profile_field_guid")

    def _build_profile_fields(self):
        profile_field1 = ProfileField.objects.create(key='text_key', name='text_name', field_type='text_field')
        profile_field2 = ProfileField.objects.create(key='text_key2', name='text_name2', field_type='text_field')

        cache.set("%s%s" % (connection.schema_name, 'PROFILE_SECTIONS'),
                  [{"name": "section_one", "profileFieldGuids": [profile_field1.guid, profile_field2.guid]}]
                  )
        return [profile_field1, profile_field2]

    def test_edit_group_member_fields(self):
        profile_field1, profile_field2 = self._build_profile_fields()

        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        guid
                        showMemberProfileFields {
                            guid
                            name
                        }
                    }
                }
            }
        """

        variables = {
            "group": {
                "guid": self.group.guid,
                "showMemberProfileFieldGuids": [profile_field1.guid, profile_field2.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        data = result[1]["data"]

        self.assertEqual(data["editGroup"]["group"]["guid"], variables["group"]["guid"])
        self.assertEqual(len(data["editGroup"]["group"]["showMemberProfileFields"]), 2)
        self.assertEqual(data["editGroup"]["group"]["showMemberProfileFields"][0]["guid"], profile_field1.guid)
        self.assertEqual(data["editGroup"]["group"]["showMemberProfileFields"][1]["guid"], profile_field2.guid)

        variables = {
            "group": {
                "guid": self.group.guid,
                "showMemberProfileFieldGuids": [profile_field2.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables}, context_value={"request": request})

        data = result[1]["data"]

        self.assertEqual(data["editGroup"]["group"]["guid"], variables["group"]["guid"])
        self.assertEqual(len(data["editGroup"]["group"]["showMemberProfileFields"]), 1)
        self.assertEqual(data["editGroup"]["group"]["showMemberProfileFields"][0]["guid"], profile_field2.guid)

    def test_group_can_be_hidden_with_site_admin_perms(self):
        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        guid
                        isHidden
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid,
                "isHidden": True,
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema,
                              {"query": mutation, "variables": variables},
                              context_value={"request": request})

        data = result[1]["data"]

        # Expect is_hidden is set to True like requested
        self.assertEqual(data["editGroup"]["group"]["isHidden"],
                         variables["group"]["isHidden"])

    def test_group_cannot_be_hidden_without_site_admin_perms(self):
        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        guid
                        isHidden
                    }
                }
            }
        """
        variables = {
            "group": {
                "guid": self.group.guid,
                "isHidden": True,
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema,
                              {"query": mutation, "variables": variables},
                              context_value={"request": request})
        data = result[1]["data"]

        # Expect is_hidden is not set to True like requested
        self.assertFalse(data["editGroup"]["group"]["isHidden"])

    def test_edit_required_profile_fields(self):
        profile_field1, profile_field2 = self._build_profile_fields()

        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        guid
                        requiredProfileFields {
                            guid
                            name
                        }
                    }
                }
            }
        """

        variables = {
            "group": {
                "guid": self.group.guid,
                "requiredProfileFieldGuids": [profile_field1.guid]
            }
        }

        request = HttpRequest()
        request.user = self.user

        success, result = graphql_sync(schema, {"query": mutation, "variables": variables},
                                       context_value={"request": request})

        self.assertTrue(success, msg=result)

        from core.models.group import GroupProfileFieldSetting
        required_fields = [obj.profile_field.guid for obj in
                           GroupProfileFieldSetting.objects.filter(is_required=True, group=self.group)]
        self.assertEqual(len(required_fields), 1,
                         msg="We expected exactly one result as required GroupProfileFieldSetting")
        self.assertEqual(required_fields, [profile_field1.guid],
                         msg="We expected the first profile field as required GroupProfileFieldSetting")

    def test_edit_required_profile_fields_help_message(self):
        EXPECTED_MESSAGE = "I'd expect it to look like this"

        mutation = """
            mutation ($group: editGroupInput!) {
                editGroup(input: $group) {
                    group {
                        guid
                        requiredProfileFieldsMessage
                    }
                }
            }
        """

        variables = {
            "group": {
                "guid": self.group.guid,
                "requiredProfileFieldsMessage": EXPECTED_MESSAGE
            }
        }

        request = HttpRequest()
        request.user = self.user

        success, result = graphql_sync(schema, {"query": mutation, "variables": variables},
                                       context_value={"request": request})

        self.assertTrue(success, msg=result)

        self.group.refresh_from_db()
        self.assertEqual(self.group.required_fields_message, EXPECTED_MESSAGE, msg="De inhoud van required_fields_message wordt niet goed geupdate.")
