from unittest.mock import MagicMock, patch

from ariadne import graphql_sync
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.files import File
from django.http import HttpRequest
from core.models.attachment import Attachment
from core.models.widget import Widget
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from backend2.schema import schema
from cms.models import Column, Page, Row
from core.constances import USER_ROLES
from user.models import User


class AddWidgetTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.editor = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.user = mixer.blend(User)
        self.page = mixer.blend(Page)
        self.row = mixer.blend(Row, position=0, page=self.page)
        self.column1 = mixer.blend(Column, position=1, row=self.row, page=self.page, width=[6])

    @patch("core.lib.get_mimetype")
    @patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_widget_to_column_by_admin(self, mock_open, mock_mimetype):
        file_mock = MagicMock(spec=File)
        file_mock.name = 'test.png'
        file_mock.content_type = 'image/png'

        mock_open.return_value = file_mock
        mock_mimetype.return_value = file_mock.content_type

        mutation = """
            mutation AddWidget($widgetInput: addWidgetInput!) {
                addWidget(input: $widgetInput) {
                    widget {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        settings {
                            key
                            value
                            richDescription
                            attachment {
                                id
                                mimeType
                                url
                                name
                            }
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "widgetInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.column1.guid,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1", "attachment": "test.png"}, {"key": "key2", "value": "value2", "attachment": "test.png"}],
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        attachment = Attachment.objects.get(id=data["addWidget"]["widget"]["settings"][0]['attachment']['id'])
        widget = Widget.objects.get(id=data["addWidget"]["widget"]["guid"])

        self.assertEqual(data["addWidget"]["widget"]["position"], 1)
        self.assertEqual(data["addWidget"]["widget"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addWidget"]["widget"]["parentGuid"], self.column1.guid)
        self.assertEqual(data["addWidget"]["widget"]["canEdit"], True)
        self.assertEqual(data["addWidget"]["widget"]["settings"][0]['attachment']['name'], "test.png")
        self.assertEqual(data["addWidget"]["widget"]["settings"][0]['attachment']['url'], attachment.url)
        self.assertEqual(attachment.attached, widget)

    def test_add_widget_to_column_by_editor(self):

        mutation = """
            mutation AddWidget($widgetInput: addWidgetInput!) {
                addWidget(input: $widgetInput) {
                    widget {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "widgetInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.column1.guid,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}],
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.editor

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addWidget"]["widget"]["position"], 1)
        self.assertEqual(data["addWidget"]["widget"]["containerGuid"], self.page.guid)
        self.assertEqual(data["addWidget"]["widget"]["parentGuid"], self.column1.guid)
        self.assertEqual(data["addWidget"]["widget"]["canEdit"], True)

    def test_add_widget_to_column_by_anonymous(self):

        mutation = """
            mutation AddWidget($widgetInput: addWidgetInput!) {
                addWidget(input: $widgetInput) {
                    widget {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "widgetInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.column1.guid,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}],
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_logged_in")


    def test_add_widget_to_column_by_user(self):

        mutation = """
            mutation AddWidget($widgetInput: addWidgetInput!) {
                addWidget(input: $widgetInput) {
                    widget {
                        guid
                        position
                        containerGuid
                        parentGuid
                        canEdit
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "widgetInput": {
                "containerGuid": self.page.guid,
                "parentGuid": self.column1.guid,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}],
                "position": 1
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
