from unittest import mock

from django.conf import settings
from django.core.files import File

from cms.factories import TextPageFactory, CampagnePageFactory
from cms.resolvers.page import resolve_rows
from core.tests.helpers import PleioTenantTestCase
from file.models import FileFolder
from user.factories import EditorFactory
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class PageTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = EditorFactory()
        self.user2 = EditorFactory()
        self.page_parent = TextPageFactory(owner=self.user1,
                                           title="Test parent page",
                                           rich_description="JSON to string")
        self.page_child = TextPageFactory(owner=self.user1,
                                          title="Test child page",
                                          rich_description="JSON to string",
                                          parent=self.page_parent)
        self.page_child2 = TextPageFactory(owner=self.user2,
                                           read_access=[ACCESS_TYPE.user.format(self.user2.id)],
                                           write_access=[ACCESS_TYPE.user.format(self.user2.id)],
                                           title="Test child page other user",
                                           rich_description="JSON to string",
                                           parent=self.page_parent)
        self.page_child_child = TextPageFactory(owner=self.user1,
                                                title="Test child of child page",
                                                rich_description="JSON to string",
                                                parent=self.page_child)

        self.query = """
            query PageItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...PageDetailFragment
                    __typename
                }
            }

            fragment PageDetailFragment on Page {
                pageType
                canEdit
                title
                url
                richDescription
                tags
                accessId
                parent {
                    guid
                }
                hasChildren
                children {
                    guid
                    title
                    canEdit
                    children {
                        guid
                        title
                        canEdit
                        children {
                            guid
                            title
                        }
                        owner {
                            guid
                            name
                        }
                    }
                    owner {
                        guid
                        name
                    }
                }
                owner {
                    guid
                    name
                }
            }
        """

    def tearDown(self):
        self.page_parent.delete()
        self.user1.delete()
        super().tearDown()

    def test_parent_page_by_anonymous(self):
        variables = {
            "guid": self.page_parent.guid
        }
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["title"], "Test parent page")
        self.assertEqual(data["entity"]["richDescription"], "JSON to string")
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["parent"], None)
        self.assertEqual(data["entity"]["hasChildren"], True)
        self.assertEqual(data["entity"]["url"], "/cms/view/{}/{}".format(self.page_parent.guid, slugify(self.page_parent.title)))
        self.assertEqual(len(data["entity"]["children"]), 1)
        self.assertEqual(data["entity"]["children"][0]["guid"], self.page_child.guid)
        self.assertEqual(data["entity"]["children"][0]["owner"]["guid"], self.user1.guid)
        self.assertEqual(data["entity"]["children"][0]["children"][0]["guid"], self.page_child_child.guid)
        self.assertEqual(data["entity"]["children"][0]["children"][0]["owner"]["guid"], self.user1.guid)
        self.assertEqual(data["entity"]["owner"]["guid"], self.user1.guid)
        self.assertEqual(data["entity"]["owner"]["name"], self.user1.name)

    def test_child_page_by_owner(self):
        variables = {
            "guid": self.page_child.guid
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)
        data = result['data']

        self.assertEqual(data["entity"]["title"], "Test child page")
        self.assertEqual(data["entity"]["richDescription"], "JSON to string")
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["parent"]["guid"], self.page_parent.guid)
        self.assertEqual(data["entity"]["hasChildren"], True)
        self.assertEqual(data["entity"]["url"], "/cms/view/{}/{}".format(self.page_child.guid, slugify(self.page_child.title)))
        self.assertEqual(data["entity"]["children"][0]["guid"], self.page_child_child.guid)
        self.assertEqual(data["entity"]["owner"]["guid"], self.user1.guid)
        self.assertEqual(data["entity"]["owner"]["name"], self.user1.name)


class TestCampagnePageTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.owner = EditorFactory()
        self.ROWS = [
            {"isFullWidth": False,
             "backgroundColor": "orange",
             "columns": [
                 {"width": [1],
                  "widgets": [
                      {"type": "title",
                       "settings": [
                           {"key": "title",
                            "value": "Foo",
                            "richDescription": None,
                            "attachment": None}
                       ]},
                  ]}
             ]},
            {"isFullWidth": False,
             "backgroundColor": "orange",
             "columns": []}
        ]
        self.page = CampagnePageFactory(owner=self.owner,
                                        row_repository=self.ROWS)
        self.query = """
            query PageItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    ...PageDetailFragment
                    __typename
                }
            }

            fragment PageDetailFragment on Page {
                pageType
                title
                owner {
                    guid
                    name
                }
                rows {
                    isFullWidth
                    backgroundColor
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
        """
        self.variables = {
            'guid': self.page.guid
        }

    def tearDown(self):
        self.page.delete()
        self.owner.delete()
        super().tearDown()

    def test_load_campagne_page(self):
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.query, self.variables)
        entity = result['data']['entity']

        self.assertEqual(entity['guid'], self.page.guid)
        self.assertEqual(entity['pageType'], 'campagne')
        self.assertEqual(entity['title'], self.page.title)
        self.assertEqual(entity['owner']['guid'], self.owner.guid)
        self.assertEqual(entity['rows'], [self.ROWS[0]])


class TestPagePropertiesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = EditorFactory()
        self.page = CampagnePageFactory(owner=self.owner)

    def create_attachment(self):
        self.file_mock = mock.MagicMock(spec=File)
        self.file_mock.name = 'attachment.jpg'
        self.file_mock.content_type = 'image/jpg'

        self.get_mimetype = mock.patch("core.lib.get_mimetype").start()
        self.get_mimetype.return_value = self.file_mock.content_type

        self.file_open = mock.patch("{}.open".format(settings.DEFAULT_FILE_STORAGE)).start()
        self.file_open.return_value = self.file_mock
        return FileFolder.objects.create(upload="attachment.jpg", owner=self.owner)

    def test_zero_attachments_via_rows(self):
        found_attachments = [a_pk for a_pk in self.page.lookup_attachments()]
        self.assertQuerysetEqual(found_attachments, [])

    def test_one_attachment_via_rows(self):
        attachment = self.create_attachment()
        self.page.row_repository = [
            {"columns": [
                {"widgets": [
                    {"settings": [
                        {"attachmentId": str(attachment.id)}
                    ]}
                ]}
            ]}
        ]
        found_attachments = [a_pk for a_pk in self.page.lookup_attachments()]
        self.assertQuerysetEqual(found_attachments, [str(attachment.pk)])

    def test_rich_text_fields(self):
        self.page.rich_description = self.tiptap_paragraph("rich_description")
        self.page.row_repository = [
            {'columns': [
                {"widgets": [
                    {'settings': [
                        {'richDescription': self.tiptap_paragraph("widget_rich_description")}]
                    }]
                }]
            }
        ]

        self.assertEqual(self.page.rich_fields, [
            self.tiptap_paragraph("rich_description"),
            self.tiptap_paragraph("widget_rich_description")
        ])
