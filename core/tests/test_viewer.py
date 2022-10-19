from core.factories import GroupFactory
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory, UserFactory
from wiki.factories import WikiFactory
from core.constances import USER_ROLES


class ViewerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = UserFactory(has_2fa_enabled=False)
        self.groupOwner = UserFactory()
        self.groupAdmin = UserFactory()
        self.groupUser = UserFactory()
        self.groupUserWiki = UserFactory()
        self.authenticatedAdminUser = AdminFactory(has_2fa_enabled=True)
        self.group: Group = GroupFactory(owner=self.groupOwner)
        self.group.join(self.groupAdmin, 'admin')
        self.group.join(self.groupUserWiki)
        self.group.join(self.groupUser)
        self.wiki = WikiFactory(owner=self.groupUserWiki, group=self.group)
        self.query = """
            query viewer($container: String, $wikiGuid: String){
                viewer {
                    guid
                    loggedIn
                    isSubEditor
                    isAdmin
                    isBanned
                    has2faEnabled
                    user {
                        guid
                        email
                        name
                    }
                }
                blog: viewer {
                    canWriteToContainer(subtype: "blog")
                }
                groupBlog: viewer {
                    canWriteToContainer(subtype: "blog", containerGuid: $container)
                }
                news: viewer {
                    canWriteToContainer(subtype: "news")
                }
                groupNews: viewer {
                    canWriteToContainer(subtype: "news", containerGuid: $container)
                }
                specificGroupWiki: viewer {
                    canWriteToContainer(subtype: "wiki", containerGuid: $wikiGuid)
                }
            }
        """
        self.variables = {
            "container": self.group.guid,
            "wikiGuid": self.wiki.guid,
        }
        self.query_container = """
            query canWriteToContainer($guid: String, $subtype: String){
                viewer {
                    canWriteToContainer(
                        containerGuid: $guid
                        subtype: $subtype
                    )
                }
            }
        """
        self.container_variables = {
            "guid": self.group.guid,
            "subtype": "blog",
        }

    def tearDown(self):
        self.group.delete()
        self.groupUser.delete()
        self.authenticatedUser.delete()
        self.authenticatedAdminUser.delete()
        super().tearDown()

    def test_viewer_anonymous(self):
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]
        self.assertEqual(data["viewer"]["guid"], "viewer:0")
        self.assertEqual(data["viewer"]["loggedIn"], False)
        self.assertEqual(data["viewer"]["isSubEditor"], False)
        self.assertEqual(data["viewer"]["isAdmin"], False)
        self.assertEqual(data["viewer"]["has2faEnabled"], False)
        self.assertIsNone(data["viewer"]["user"])

        self.assertEqual(data['blog']['canWriteToContainer'], False)
        self.assertEqual(data['news']['canWriteToContainer'], False)
        self.assertEqual(data['groupBlog']['canWriteToContainer'], False)
        self.assertEqual(data['groupNews']['canWriteToContainer'], False)
        self.assertEqual(data['specificGroupWiki']['canWriteToContainer'], False)

    def test_viewer_loggedin(self):
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]
        self.assertEqual(data["viewer"]["guid"], "viewer:{}".format(self.authenticatedUser.id))
        self.assertEqual(data["viewer"]["loggedIn"], True)
        self.assertEqual(data["viewer"]["isSubEditor"], self.authenticatedUser.has_role(USER_ROLES.EDITOR) or self.authenticatedUser.has_role(USER_ROLES.ADMIN))
        self.assertEqual(data["viewer"]["isAdmin"], self.authenticatedUser.has_role(USER_ROLES.ADMIN))
        self.assertEqual(data["viewer"]["has2faEnabled"], False)
        self.assertEqual(data["viewer"]["user"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["viewer"]["user"]["email"], self.authenticatedUser.email)

        self.assertEqual(data['blog']['canWriteToContainer'], True)
        self.assertEqual(data['news']['canWriteToContainer'], False)
        self.assertEqual(data['groupBlog']['canWriteToContainer'], False)
        self.assertEqual(data['groupNews']['canWriteToContainer'], False)
        self.assertEqual(data['specificGroupWiki']['canWriteToContainer'], False)

    def test_viewer_loggedin_admin(self):
        self.graphql_client.force_login(self.authenticatedAdminUser)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]
        self.assertEqual(data["viewer"]["guid"], "viewer:{}".format(self.authenticatedAdminUser.id))
        self.assertEqual(data["viewer"]["loggedIn"], True)
        self.assertEqual(data["viewer"]["isSubEditor"],
                         self.authenticatedAdminUser.has_role(USER_ROLES.EDITOR) or self.authenticatedAdminUser.has_role(USER_ROLES.ADMIN))
        self.assertEqual(data["viewer"]["isAdmin"], self.authenticatedAdminUser.has_role(USER_ROLES.ADMIN))
        self.assertEqual(data["viewer"]["isBanned"], False)
        self.assertEqual(data["viewer"]["has2faEnabled"], True)
        self.assertEqual(data["viewer"]["user"]["name"], self.authenticatedAdminUser.name)
        self.assertEqual(data["viewer"]["user"]["guid"], self.authenticatedAdminUser.guid)

        self.assertEqual(data['blog']['canWriteToContainer'], True)
        self.assertEqual(data['news']['canWriteToContainer'], True)
        self.assertEqual(data['groupBlog']['canWriteToContainer'], True)
        self.assertEqual(data['groupNews']['canWriteToContainer'], True)
        self.assertEqual(data['specificGroupWiki']['canWriteToContainer'], True)

    def test_viewer_loggedin_group_user(self):
        self.graphql_client.force_login(self.groupUser)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]
        self.assertEqual(data['blog']['canWriteToContainer'], True)
        self.assertEqual(data['news']['canWriteToContainer'], False)
        self.assertEqual(data['groupBlog']['canWriteToContainer'], True)
        self.assertEqual(data['groupNews']['canWriteToContainer'], True)
        self.assertEqual(data['specificGroupWiki']['canWriteToContainer'], False)

    def test_viewer_can_write_to_container_groupwikiowner(self):
        self.graphql_client.force_login(self.groupUserWiki)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]
        self.assertEqual(data['blog']['canWriteToContainer'], True)
        self.assertEqual(data['news']['canWriteToContainer'], False)
        self.assertEqual(data['groupBlog']['canWriteToContainer'], True)
        self.assertEqual(data['groupNews']['canWriteToContainer'], True)

        # Klopt dit? Hij zou toch moeten kunnen schrijven?
        self.assertEqual(data['specificGroupWiki']['canWriteToContainer'], True)

    def test_viewer_can_write_to_container_admin(self):
        self.graphql_client.force_login(self.groupAdmin)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]
        self.assertEqual(data['blog']['canWriteToContainer'], True)
        self.assertEqual(data['news']['canWriteToContainer'], False)
        self.assertEqual(data['groupBlog']['canWriteToContainer'], True)
        self.assertEqual(data['groupNews']['canWriteToContainer'], True)
        self.assertEqual(data['specificGroupWiki']['canWriteToContainer'], True)

    def test_viewer_can_write_to_container_user_self(self):
        self.container_variables['guid'] = self.authenticatedUser.guid
        self.container_variables['subype'] = "file"

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query_container, self.container_variables)

        data = result["data"]
        self.assertEqual(data["viewer"]["canWriteToContainer"], True)

    def test_viewer_can_not_write_to_container_user_other(self):
        self.container_variables['guid'] = self.groupOwner.guid
        self.container_variables['subype'] = "file"

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query_container, self.container_variables)

        data = result["data"]
        self.assertEqual(data["viewer"]["canWriteToContainer"], False)

    def test_admin_viewer_can_write_to_user_container(self):
        self.container_variables['guid'] = self.authenticatedUser.guid
        self.container_variables['subype'] = "file"

        self.graphql_client.force_login(self.authenticatedAdminUser)
        result = self.graphql_client.post(self.query_container, self.container_variables)

        data = result["data"]
        self.assertEqual(data["viewer"]["canWriteToContainer"], True)
