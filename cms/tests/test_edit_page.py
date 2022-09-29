from django.utils.timezone import localtime

from core.models import Revision
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from cms.models import Page


class EditPageTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.editor = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.page: Page = mixer.blend(Page,
                                      page_type='text',
                                      owner=self.user,
                                      read_access=[ACCESS_TYPE.public],
                                      write_access=[ACCESS_TYPE.user.format(self.user.id)])
        self.campagne: Page = mixer.blend(Page,
                                          page_type='campagne',
                                          owner=self.user,
                                          read_access=[ACCESS_TYPE.public],
                                          write_access=[ACCESS_TYPE.user.format(self.user.id)])

        self.mutation = """
            mutation EditPage($input: editPageInput!) {
                editPage(input: $input) {
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
                "guid": self.page.guid,
                "title": "test",
                "accessId": 1,
                "tags": ['tag_1'],
                "richDescription": '{"blocks":[{"key":"6sb64","text":"test","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{}}],"entityMap":{}}'
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
