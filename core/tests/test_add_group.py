from django.db import connection
from django.conf import settings
from django.core.cache import cache
from django.core.files import File

from core import override_local_config
from core.models import ProfileField
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from unittest import mock


class AddGroupCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.admin = AdminFactory()
        self.profile_field = ProfileField.objects.create(key='profile_field', name='text_name', field_type='text_field')


        self.mutation = """
            mutation ($group: addGroupInput!) {
                addGroup(input: $group) {
                    group {
                        guid
                        name
                        icon
                        richDescription
                        introduction
                        isIntroductionPublic
                        welcomeMessage
                        requiredProfileFieldsMessage
                        isClosed
                        isHidden
                        isMembershipOnRequest
                        isFeatured
                        isSubmitUpdatesEnabled
                        autoNotification
                        tags
                        isLeavingGroupDisabled
                        isAutoMembershipEnabled
                        requiredProfileFields {
                            guid
                        }
                        showMemberProfileFields {
                            guid
                            name
                        }
                        defaultTags
                        defaultTagCategories {
                            name
                            values
                        }
                    }
                }
            }
        """

        self.data = {
            "group": {
                "name": "Name",
                "icon": "icon.png",
                "richDescription": self.tiptap_paragraph("richDescription"),
                "introduction": "introductionMessage",
                "isIntroductionPublic": False,
                "welcomeMessage": "welcomeMessage",
                "isClosed": True,
                "isMembershipOnRequest": True,
                "isFeatured": True,
                "isAutoMembershipEnabled": True,
                "isLeavingGroupDisabled": True,
                "autoNotification": True,
                "isHidden": True,
                "requiredProfileFieldsMessage": "I'd expect this message for requiredProfileFieldsMessage",
                "tags": ["tag_one", "tag_two"],
                "requiredProfileFieldGuids": [self.profile_field.guid],
                "defaultTags": ['tag_one', 'tag_three'],
                'defaultTagCategories': [{'name': 'Test', 'values': ['One', 'Two']}]
            }
        }

    @mock.patch("core.resolvers.scalar.Tiptap")
    def test_add_group_anon(self, mock_tiptap):
        variables = self.data

        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation, variables)

        mock_tiptap.assert_called_once_with(self.data['group']['richDescription'])
        mock_tiptap.return_value.check_for_external_urls.assert_called_once_with()

    @mock.patch("core.lib.get_mimetype")
    @mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_group(self, mock_open, mock_mimetype):
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'icon.png'
        file_mock.content_type = 'image/png'
        file_mock.download = '/icon.png'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        cache.set("%s%s" % (connection.schema_name, 'LIMITED_GROUP_ADD'), False)

        variables = self.data

        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.mutation, variables)

        data = result.get("data")
        self.assertEqual(data["addGroup"]["group"]["name"], variables["group"]["name"])
        self.assertIn('/icon.png', data["addGroup"]["group"]["icon"])
        self.assertEqual(data["addGroup"]["group"]["richDescription"], variables["group"]["richDescription"])
        self.assertEqual(data["addGroup"]["group"]["introduction"], variables["group"]["introduction"])
        self.assertEqual(data["addGroup"]["group"]["isIntroductionPublic"], variables["group"]["isIntroductionPublic"])
        self.assertEqual(data["addGroup"]["group"]["welcomeMessage"], variables["group"]["welcomeMessage"])
        self.assertEqual(data["addGroup"]["group"]["requiredProfileFieldsMessage"],
                         variables["group"]["requiredProfileFieldsMessage"])
        self.assertEqual(data["addGroup"]["group"]["isClosed"], variables["group"]["isClosed"])
        self.assertEqual(data["addGroup"]["group"]["isHidden"], variables["group"]["isHidden"])
        self.assertEqual(data["addGroup"]["group"]["isMembershipOnRequest"],
                         variables["group"]["isMembershipOnRequest"])
        self.assertEqual(data["addGroup"]["group"]["isFeatured"], False)
        self.assertEqual(data["addGroup"]["group"]["isLeavingGroupDisabled"], False)
        self.assertEqual(data["addGroup"]["group"]["isAutoMembershipEnabled"], False)
        self.assertEqual(data["addGroup"]["group"]["isSubmitUpdatesEnabled"], False)
        self.assertEqual(data["addGroup"]["group"]["autoNotification"], variables["group"]["autoNotification"])
        self.assertEqual(data["addGroup"]["group"]["tags"], ["tag_one", "tag_two"])
        self.assertEqual(data["addGroup"]["group"]["requiredProfileFields"], [{"guid": self.profile_field.guid}])
        self.assertEqual(data["addGroup"]["group"]["defaultTags"], variables['group']['defaultTags'])
        self.assertEqual(data["addGroup"]["group"]["defaultTagCategories"], variables['group']['defaultTagCategories'])

        cache.clear()

    @override_local_config(LIMITED_GROUP_ADD=True)
    def test_add_group_limited_group_add(self):
        variables = self.data
        with self.assertGraphQlError('not_authorized'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, variables)

    @mock.patch("core.lib.get_mimetype")
    @mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_group_by_admin(self, mock_open, mock_mimetype):
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'icon.png'
        file_mock.content_type = 'image/png'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        variables = self.data

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["addGroup"]["group"]["name"], variables["group"]["name"])
        self.assertIn('/icon.png', data["addGroup"]["group"]["icon"])
        self.assertEqual(data["addGroup"]["group"]["richDescription"], variables["group"]["richDescription"])
        self.assertEqual(data["addGroup"]["group"]["introduction"], variables["group"]["introduction"])
        self.assertEqual(data["addGroup"]["group"]["welcomeMessage"], variables["group"]["welcomeMessage"])
        self.assertEqual(data["addGroup"]["group"]["isClosed"], variables["group"]["isClosed"])
        self.assertEqual(data["addGroup"]["group"]["isFeatured"], True)
        self.assertEqual(data["addGroup"]["group"]["isMembershipOnRequest"],
                         variables["group"]["isMembershipOnRequest"])
        self.assertEqual(data["addGroup"]["group"]["isLeavingGroupDisabled"], True)
        self.assertEqual(data["addGroup"]["group"]["isAutoMembershipEnabled"], True)
        self.assertEqual(data["addGroup"]["group"]["autoNotification"], variables["group"]["autoNotification"])
        self.assertEqual(data["addGroup"]["group"]["tags"], ["tag_one", "tag_two"])

    def test_add_group_member_fields(self):
        profile_field1 = ProfileField.objects.create(key='text_key', name='text_name', field_type='text_field')

        cache.set("%s%s" % (connection.schema_name, 'PROFILE_SECTIONS'),
                  [{"name": "section_one", "profileFieldGuids": [profile_field1.guid]}]
                  )

        variables = {
            "group": {
                "name": "Test123",
                "showMemberProfileFieldGuids": [str(profile_field1.id)]
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        data = result["data"]
        self.assertEqual(data["addGroup"]["group"]["name"], variables["group"]["name"])
        self.assertEqual(len(data["addGroup"]["group"]["showMemberProfileFields"]), 1)
        self.assertEqual(data["addGroup"]["group"]["showMemberProfileFields"][0]["guid"], profile_field1.guid)

    def test_add_prohibited_member_fields(self):
        profile_field1 = ProfileField.objects.create(key='text_key', name='text_name', field_type='html_field')

        cache.set("%s%s" % (connection.schema_name, 'PROFILE_SECTIONS'),
                  [{"name": "section_one", "profileFieldGuids": [profile_field1.guid]}]
                  )

        variables = {
            "group": {
                "name": "Test123",
                "showMemberProfileFieldGuids": [str(profile_field1.id)]
            }
        }

        with self.assertGraphQlError("Long text fields are not allowed to display on the member page."):
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, variables)
