from django.conf import settings
from django.core.files import File
from unittest import mock

from cms.factories import TextPageFactory
from core.models import Attachment
from core.tests.helpers import PleioTenantTestCase
from user.factories import EditorFactory, AdminFactory, UserFactory


class AddTextPageTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.admin = AdminFactory()
        self.editor = EditorFactory()
        self.page = TextPageFactory(owner=self.editor)

        self.mutation = """
            mutation AddPage($input: addPageInput!) {
                addPage(input: $input) {
                    entity {
                        guid
                        ... on Page {
                            pageType
                            canEdit
                            title
                            url
                            richDescription
                            tags
                            parent {
                                guid
                            }
                            accessId
                        }
                    }
                    __typename
                }
            }
        """

        self.variables = {
            "input": {
                "title": "text",
                "pageType": "text",
                "accessId": 1,
                "tags": [],
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'
            }
        }

    def test_add_page(self):
        for user, msg in ((self.admin, 'as admin'),
                          (self.editor, 'as editor')):
            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.mutation, self.variables)

            entity = result['data']['addPage']['entity']
            self.assertEqual(entity["title"], "text", msg=msg)
            self.assertEqual(entity["richDescription"],
                             '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}',
                             msg=msg)
            self.assertEqual(entity["pageType"], "text", msg=msg)
            self.assertEqual(entity["tags"], [], msg=msg)
            self.assertEqual(entity["accessId"], 1, msg=msg)
            self.assertEqual(entity["canEdit"], True, msg=msg)

    def test_add_sub_page(self):
        self.variables['input']["containerGuid"] = self.page.guid
        for user, msg in ((self.admin, 'as admin'),
                          (self.editor, 'as editor')):
            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.mutation, self.variables)

            entity = result['data']['addPage']['entity']
            self.assertEqual(entity["parent"]["guid"], self.page.guid, msg=msg)

    def test_add_page_by_anonymous(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation, self.variables)

    def test_add_page_by_user(self):
        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)


class AddCampagnePageTestCase(PleioTenantTestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.admin = AdminFactory()
        self.editor = EditorFactory()

        self.mutation = """
            mutation AddPage($input: addPageInput!) {
                addPage(input: $input) {
                    entity {
                        guid
                        ... on Page {
                            pageType
                            canEdit
                            title
                            url
                            richDescription
                            tags
                            parent {
                                guid
                            }
                            accessId
                            rows {
                                isFullWidth
                                columns {
                                    width
                                    widgets {
                                        type
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
                                    }
                                }
                            }
                        }
                    }
                    __typename
                }
            }
        """

        self.variables = {
            "input": {
                "title": "test",
                "pageType": "campagne",
                "accessId": 1,
                "tags": [],
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}',
            }
        }

    def test_add_campaign_page_by_admin(self):
        for user, msg in ((self.admin, 'as admin'),
                          (self.editor, 'as editor')):
            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.mutation, self.variables)
            entity = result['data']['addPage']['entity']

            self.assertEqual(entity["title"], "test", msg=msg)
            self.assertEqual(entity["richDescription"],
                             '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}',
                             msg=msg)
            self.assertEqual(entity["pageType"], "campagne", msg=msg)
            self.assertEqual(entity["tags"], [], msg=msg)
            self.assertEqual(entity["accessId"], 1, msg=msg)
            self.assertEqual(entity["canEdit"], True, msg=msg)
            self.assertEqual(entity["parent"], None, msg=msg)

    def test_add_campaign_page_by_anonymous(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation, self.variables)

    def test_add_campaign_page_by_user(self):
        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)

    @mock.patch("core.models.Attachment.scan")
    @mock.patch("core.lib.get_mimetype")
    @mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_add_page_with_widgets(self, mocked_open, mocked_mimetype, mocked_scan):
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'attachment.jpg'
        file_mock.content_type = 'image/jpg'

        mocked_open.return_value = file_mock
        mocked_mimetype.return_value = file_mock.content_type

        self.variables['input']['rows'] = [
            {"isFullWidth": True,
             "columns": [
                 {"widgets": [{
                     "type": 'demo',
                     "settings": [
                         {"key": 'title',
                          "value": "Demo widget"},
                         {"key": 'richDescription',
                          "richDescription": self.tiptap_paragraph("Some description")},
                         {"key": 'attachment',
                          "attachment": 'attachment.jpg'}
                     ]}
                 ]}
             ]}
        ]

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)
        rows = result['data']["addPage"]["entity"]["rows"]
        expected_attachment: Attachment = Attachment.objects.first()
        self.assertDictEqual({"data": rows}, {"data": [
            {"isFullWidth": True,
             "columns": [
                 {"width": None,
                  "widgets": [
                      {"type": "demo",
                       "settings": [
                           {"key": 'title',
                            "value": "Demo widget",
                            "richDescription": None,
                            "attachment": None},
                           {"key": "richDescription",
                            "value": None,
                            "richDescription": self.tiptap_paragraph("Some description"),
                            "attachment": None},
                           {"key": "attachment",
                            "value": None,
                            "richDescription": None,
                            "attachment": {
                                "id": str(expected_attachment.id),
                                "mimeType": expected_attachment.mime_type,
                                "name": expected_attachment.name,
                                "url": expected_attachment.url
                            }}
                       ]}
                  ]}
             ]}
        ]})
        self.assertTrue(mocked_scan.called)
