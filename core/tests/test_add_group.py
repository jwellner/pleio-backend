from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from core import config
from django.conf import settings
from django.core.cache import cache
from django.core.files import File
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError
from unittest.mock import patch, MagicMock


class AddGroupCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=['ADMIN'])

        self.data = {
            "group": {
                "name": "Name",
                "icon": "icon.png",
                "description": "description",
                "richDescription": "<p>richDescription</p>",
                "introduction": "introductionMessage",
                "isIntroductionPublic": False,
                "welcomeMessage": "welcomeMessage",
                "isClosed": True,
                "isMembershipOnRequest": True,
                "isFeatured": True,
                "isAutoMembershipEnabled": True,
                "isLeavingGroupDisabled": True,
                "autoNotification": True,
                "tags": ["tag_one", "tag_two"]
            }
        }

    def test_add_group_anon(self):

        mutation = """
            mutation ($group: addGroupInput!) {
                addGroup(input: $group) {
                    group {
                        guid
                        name
                        icon
                        description
                        richDescription
                        introduction
                        welcomeMessage
                        isClosed
                        isMembershipOnRequest
                        isFeatured
                        autoNotification
                        tags
                        isLeavingGroupDisabled
                        isAutoMembershipEnabled
                    }
                }
            }
        """
        variables = self.data

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")

    @patch("file.models.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_group(self, mock_open, mock_mimetype):

        file_mock = MagicMock(spec=File)
        file_mock.name = 'icon.png'
        file_mock.content_type = 'image/png'
        file_mock.download = '/icon.png'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        cache.set("%s%s" % (connection.schema_name, 'LIMITED_GROUP_ADD'), False)

        mutation = """
            mutation ($group: addGroupInput!) {
                addGroup(input: $group) {
                    group {
                        guid
                        name
                        icon
                        description
                        richDescription
                        introduction
                        isIntroductionPublic
                        welcomeMessage
                        isClosed
                        isMembershipOnRequest
                        isFeatured
                        autoNotification
                        tags
                        isLeavingGroupDisabled
                        isAutoMembershipEnabled
                    }
                }
            }
        """
        variables = self.data

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addGroup"]["group"]["name"], variables["group"]["name"])
        self.assertIn('/icon.png', data["addGroup"]["group"]["icon"])
        self.assertEqual(data["addGroup"]["group"]["description"], variables["group"]["description"])
        self.assertEqual(data["addGroup"]["group"]["richDescription"], variables["group"]["richDescription"])
        self.assertEqual(data["addGroup"]["group"]["introduction"], variables["group"]["introduction"])
        self.assertEqual(data["addGroup"]["group"]["isIntroductionPublic"], variables["group"]["isIntroductionPublic"])
        self.assertEqual(data["addGroup"]["group"]["welcomeMessage"], variables["group"]["welcomeMessage"])
        self.assertEqual(data["addGroup"]["group"]["isClosed"], variables["group"]["isClosed"])
        self.assertEqual(data["addGroup"]["group"]["isMembershipOnRequest"], variables["group"]["isMembershipOnRequest"])
        self.assertEqual(data["addGroup"]["group"]["isFeatured"], False)
        self.assertEqual(data["addGroup"]["group"]["isLeavingGroupDisabled"], False)
        self.assertEqual(data["addGroup"]["group"]["isAutoMembershipEnabled"], False)
        self.assertEqual(data["addGroup"]["group"]["autoNotification"], variables["group"]["autoNotification"])
        self.assertEqual(data["addGroup"]["group"]["tags"], ["tag_one", "tag_two"])

        cache.clear()

    def test_add_group_limited_group_add(self):

        mutation = """
            mutation ($group: addGroupInput!) {
                addGroup(input: $group) {
                    group {
                        guid
                        name
                        icon
                        description
                        richDescription
                        introduction
                        welcomeMessage
                        isClosed
                        isMembershipOnRequest
                        isFeatured
                        autoNotification
                        tags
                        isLeavingGroupDisabled
                        isAutoMembershipEnabled
                    }
                }
            }
        """
        variables = self.data

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    @patch("file.models.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_group_by_admin(self, mock_open, mock_mimetype):

        file_mock = MagicMock(spec=File)
        file_mock.name = 'icon.png'
        file_mock.content_type = 'image/png'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        mutation = """
            mutation ($group: addGroupInput!) {
                addGroup(input: $group) {
                    group {
                        guid
                        name
                        icon
                        description
                        richDescription
                        introduction
                        welcomeMessage
                        isClosed
                        isMembershipOnRequest
                        isFeatured
                        autoNotification
                        isLeavingGroupDisabled
                        isAutoMembershipEnabled
                        tags
                    }
                }
            }
        """
        variables = self.data

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        #self(data["addGroup"]["group"]["guid"], 'group:')
        self.assertEqual(data["addGroup"]["group"]["name"], variables["group"]["name"])
        self.assertIn('/icon.png', data["addGroup"]["group"]["icon"])
        self.assertEqual(data["addGroup"]["group"]["description"], variables["group"]["description"])
        self.assertEqual(data["addGroup"]["group"]["richDescription"], variables["group"]["richDescription"])
        self.assertEqual(data["addGroup"]["group"]["introduction"], variables["group"]["introduction"])
        self.assertEqual(data["addGroup"]["group"]["welcomeMessage"], variables["group"]["welcomeMessage"])
        self.assertEqual(data["addGroup"]["group"]["isClosed"], variables["group"]["isClosed"])
        self.assertEqual(data["addGroup"]["group"]["isFeatured"], True)
        self.assertEqual(data["addGroup"]["group"]["isMembershipOnRequest"], variables["group"]["isMembershipOnRequest"])
        self.assertEqual(data["addGroup"]["group"]["isLeavingGroupDisabled"], True)
        self.assertEqual(data["addGroup"]["group"]["isAutoMembershipEnabled"], True)
        self.assertEqual(data["addGroup"]["group"]["autoNotification"], variables["group"]["autoNotification"])
        self.assertEqual(data["addGroup"]["group"]["tags"], ["tag_one", "tag_two"])
