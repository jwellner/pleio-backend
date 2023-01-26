from cms.factories import TextPageFactory
from core.constances import ACCESS_TYPE
from core.tests.helpers import PleioTenantTestCase
from user.factories import EditorFactory, UserFactory


class TestSubpagesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.editor = EditorFactory()
        self.visitor = UserFactory()
        self.master_page = TextPageFactory(owner=self.editor,
                                           title="master page")
        self.public_subpage = TextPageFactory(owner=self.editor, parent=self.master_page,
                                              title="public subpage",
                                              position=1)
        self.private_subpage = TextPageFactory(owner=self.editor, parent=self.master_page,
                                               read_access=[ACCESS_TYPE.user.format(self.editor.guid)],
                                               title="private subpage",
                                               position=10)

        self.query = """
        query Entity($guid: String!) {
            entity(guid: $guid) {
                ... on Page {
                    menu {
                        guid
                        title
                        children {
                            guid
                            title
                        }
                    }
                }
            }
        }
        """

        self.variables = {
            'guid': self.master_page.guid,
        }

    def test_visitor_access_to_page_menu(self):
        self.graphql_client.force_login(self.visitor)

        response = self.graphql_client.post(self.query, self.variables)
        result = response['data']['entity']

        self.assertEqual(result['menu']['guid'], self.master_page.guid)
        self.assertEqual([c['guid'] for c in result['menu']['children']], [self.public_subpage.guid])

    def test_owner_access_to_page_menu(self):
        self.graphql_client.force_login(self.editor)

        response = self.graphql_client.post(self.query, self.variables)
        result = response['data']['entity']

        self.assertEqual(result['menu']['guid'], self.master_page.guid)
        self.assertEqual([c['guid'] for c in result['menu']['children']], [self.public_subpage.guid, self.private_subpage.guid])
