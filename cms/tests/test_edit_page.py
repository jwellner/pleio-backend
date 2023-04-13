from unittest import mock

from django.conf import settings
from django.core.files import File

from cms.factories import TextPageFactory, CampagnePageFactory
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from user.factories import AdminFactory, EditorFactory, UserFactory


class EditTextPageTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.editor = EditorFactory()
        self.admin = AdminFactory()
        self.page = TextPageFactory(owner=self.editor)

        self.mutation = """
            mutation EditPage($input: editPageInput!) {
                editPage(input: $input) {
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
                        __typename
                    }
                    __typename
                }
            }
        """
        self.variables = {
            "input": {
                "guid": self.page.guid,
                "title": "test",
                "accessId": 1,
                "tags": ['tag_1'],
                "richDescription": self.tiptap_paragraph("Test123"),
            }
        }

    def assert_text_page_update_ok(self):
        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result['data']["editPage"]["entity"]

        self.assertEqual(entity["title"], self.variables['input']['title'])
        self.assertEqual(entity["richDescription"], self.variables['input']['richDescription'])
        self.assertEqual(entity["tags"], self.variables['input']['tags'])
        self.assertEqual(entity["accessId"], 1)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["parent"], None)

    def test_edit_page_by_admin(self):
        self.graphql_client.force_login(self.admin)
        self.assert_text_page_update_ok()

    def test_edit_page_by_editor(self):
        self.graphql_client.force_login(self.editor)
        self.assert_text_page_update_ok()

    def test_edit_page_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_page_by_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)


class EditCampagnePageTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.editor = EditorFactory()
        self.admin = AdminFactory()
        self.page = CampagnePageFactory(owner=self.editor)

        self.mutation = """
            mutation EditPage($input: editPageInput!) {
                editPage(input: $input) {
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
                        __typename
                    }
                    __typename
                }
            }
        """
        self.variables = {
            "input": {
                "guid": self.page.guid,
                "title": "test",
                "accessId": 1,
                "tags": ['tag_1'],
                "richDescription": self.tiptap_paragraph("Test123"),
            }
        }

    def assert_text_page_update_ok(self):
        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result['data']["editPage"]["entity"]

        self.assertEqual(entity["title"], self.variables['input']['title'])
        self.assertEqual(entity["richDescription"], self.variables['input']['richDescription'])
        self.assertEqual(entity["tags"], self.variables['input']['tags'])
        self.assertEqual(entity["accessId"], 1)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["parent"], None)
        self.assertEqual(entity["rows"], [])

    @mock.patch("file.models.FileFolder.scan")
    @mock.patch("core.lib.get_mimetype")
    @mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE))
    def test_update_rows(self, mocked_open, mocked_mimetype, mocked_scan):
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

        self.graphql_client.force_login(AdminFactory())

        result = self.graphql_client.post(self.mutation, self.variables)
        rows = result['data']["editPage"]["entity"]["rows"]
        expected_attachment: FileFolder = FileFolder.objects.first()
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
                                "name": expected_attachment.title,
                                "url": expected_attachment.attachment_url
                            }}
                       ]}
                  ]}
             ]}
        ]})
        self.assertTrue(mocked_scan.called)

    def test_edit_page_by_admin(self):
        self.graphql_client.force_login(self.admin)
        self.assert_text_page_update_ok()

    def test_edit_page_by_editor(self):
        self.graphql_client.force_login(self.editor)
        self.assert_text_page_update_ok()

    def test_edit_page_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_page_by_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)
