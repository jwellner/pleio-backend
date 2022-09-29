from core.tests.helpers import PleioTenantTestCase
from user.factories import EditorFactory, AdminFactory, UserFactory
from mixer.backend.django import mixer
from cms.models import Page


class AddPageTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.admin = AdminFactory()
        self.editor = EditorFactory()
        self.page = mixer.blend(Page)

        self.mutation = """
            mutation AddPage($input: addPageInput!) {
                addPage(input: $input) {
                    entity {
                    guid
                    ...PageDetailFragment
                    __typename
                    }
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
                parent {
                    guid
                }
                accessId
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
        self.variables_text = {
            "input": {
                "title": "text",
                "pageType": "text",
                "containerGuid": self.page.guid,
                "accessId": 1,
                "tags": [],
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'
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

    def test_add_text_sub_page_by_admin(self):
        for user, msg in ((self.admin, 'as admin'),
                          (self.editor, 'as editor')):
            self.graphql_client.force_login(user)
            result = self.graphql_client.post(self.mutation, self.variables_text)
            entity = result['data']['addPage']['entity']

            self.assertEqual(entity["title"], "text", msg=msg)
            self.assertEqual(entity["richDescription"],
                             '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}',
                             msg=msg)
            self.assertEqual(entity["pageType"], "text", msg=msg)
            self.assertEqual(entity["tags"], [], msg=msg)
            self.assertEqual(entity["accessId"], 1, msg=msg)
            self.assertEqual(entity["canEdit"], True, msg=msg)
            self.assertEqual(entity["parent"]["guid"], self.page.guid, msg=msg)

    def test_add_campaign_page_by_anonymous(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.mutation, self.variables)

    def test_add_campaign_page_by_user(self):
        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)
