from cms.factories import TextPageFactory, CampagnePageFactory
from core.tests.helpers import PleioTenantTestCase
from core.lib import get_access_id
from user.factories import AdminFactory, EditorFactory, UserFactory


class CopyTextPageTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.editor = EditorFactory()
        self.admin = AdminFactory()
        self.page = TextPageFactory(owner=self.editor)

        self.mutation = """
            mutation CopyPage($input: copyEntityInput!) {
                copyEntity(input: $input) {
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
                            owner {
                                guid
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
                "subtype": "page"
            }
        }

    def assert_text_page_copy_ok(self, user):
        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result['data']["copyEntity"]["entity"]

        self.assertNotEqual(entity["guid"], self.page.guid)
        self.assertIn(self.page.title, entity["title"])
        self.assertEqual(entity["richDescription"], self.page.rich_description)
        self.assertEqual(entity["tags"], self.page.tags)
        self.assertEqual(entity["accessId"], get_access_id(self.page.read_access))
        self.assertEqual(entity["canEdit"], self.page.can_write(user))
        self.assertEqual(entity["parent"], None)
        self.assertEqual(entity["owner"]["guid"], user.guid)

    def test_copy_page_by_admin(self):
        self.graphql_client.force_login(self.admin)
        self.assert_text_page_copy_ok(self.admin)

    def test_copy_page_by_editor(self):
        self.graphql_client.force_login(self.editor)
        self.assert_text_page_copy_ok(self.editor)

    def test_copy_page_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_copy_page_by_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)


class CopyCampagnePageTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        
        self.rows = [{
            "isFullWidth": True,
            "columns": [{
                    "widgets": [{
                    "type": 'demo',
                    "settings": [
                        {"key": 'title',
                        "value": "Demo widget"}
                    ]}
                ]}
            ]
        }]
    
        self.user = UserFactory()
        self.editor = EditorFactory()
        self.admin = AdminFactory()
        self.page = CampagnePageFactory(owner=self.editor, row_repository=self.rows)

        self.mutation = """
            mutation CopyPage($input: copyEntityInput!) {
                copyEntity(input: $input) {
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
                            owner {
                                guid
                            }
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
                "subtype": "page"
            }
        }

    def assert_text_page_update_ok(self, user):
        result = self.graphql_client.post(self.mutation, self.variables)
        entity = result['data']["copyEntity"]["entity"]

        self.assertNotEqual(entity['guid'], self.page.guid)
        self.assertIn(self.page.title, entity["title"])
        self.assertEqual(entity["richDescription"], self.page.rich_description)
        self.assertEqual(entity["tags"], self.page.tags)
        self.assertEqual(entity["accessId"], get_access_id(self.page.read_access))
        self.assertEqual(entity["canEdit"], self.page.can_write(user))
        self.assertEqual(entity["parent"], self.page.parent)
        self.assertEqual(len(entity["rows"]), len(self.page.row_repository))
        self.assertEqual(entity["owner"]["guid"], user.guid)
        self.assertEqual(entity["rows"][0]["isFullWidth"], self.rows[0]["isFullWidth"])
        self.assertEqual(entity["rows"][0]["columns"][0]["widgets"][0]["type"], "demo")

    def test_edit_page_by_admin(self):
        self.graphql_client.force_login(self.admin)
        self.assert_text_page_update_ok(self.admin)

    def test_edit_page_by_editor(self):
        self.graphql_client.force_login(self.editor)
        self.assert_text_page_update_ok(self.editor)

    def test_edit_page_by_anonymous(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_edit_page_by_user(self):
        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)
