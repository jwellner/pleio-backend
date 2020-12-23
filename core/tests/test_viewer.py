from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group
from user.models import User
from wiki.models import Wiki
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer
from core.constances import USER_ROLES

class ViewerTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.groupOwner = mixer.blend(User)
        self.groupAdmin = mixer.blend(User)
        self.groupUser = mixer.blend(User)
        self.groupUserWiki = mixer.blend(User)
        self.authenticatedAdminUser = mixer.blend(User, roles = [USER_ROLES.ADMIN])
        self.group = mixer.blend(Group, owner=self.groupOwner)
        self.group.join(self.groupOwner, 'owner')
        self.group.join(self.groupAdmin, 'owner')
        self.group.join(self.groupUser, 'member')
        self.wiki = mixer.blend(Wiki, owner=self.groupUserWiki, group=self.group)

    def tearDown(self):
        self.group.delete()
        self.groupUser.delete()
        self.authenticatedUser.delete()
        self.authenticatedAdminUser.delete()

    def test_viewer_anonymous(self):

        query = """
            {
                viewer {
                    guid
                    loggedIn
                    isSubEditor
                    isAdmin
                    user {
                        guid
                        email
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": query }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["viewer"]["guid"], "viewer:0")
        self.assertEqual(data["viewer"]["loggedIn"], False)
        self.assertEqual(data["viewer"]["isSubEditor"], False)
        self.assertEqual(data["viewer"]["isAdmin"], False)
        self.assertIsNone(data["viewer"]["user"])

    def test_viewer_loggedin(self):

        query = """
            {
                viewer {
                    guid
                    loggedIn
                    isSubEditor
                    isAdmin
                    user {
                        guid
                        email
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": query }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["viewer"]["guid"], "viewer:{}".format(self.authenticatedUser.id))
        self.assertEqual(data["viewer"]["loggedIn"], True)
        self.assertEqual(data["viewer"]["isSubEditor"], self.authenticatedUser.has_role(USER_ROLES.EDITOR) or self.authenticatedUser.has_role(USER_ROLES.ADMIN))
        self.assertEqual(data["viewer"]["isAdmin"], self.authenticatedUser.has_role(USER_ROLES.ADMIN))
        self.assertEqual(data["viewer"]["user"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["viewer"]["user"]["email"], self.authenticatedUser.email)

    def test_viewer_loggedin_admin(self):

        query = """
            {
                viewer {
                    guid
                    loggedIn
                    isSubEditor
                    isAdmin
                    isBanned
                    user {
                        guid
                        name
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedAdminUser

        result = graphql_sync(schema, { "query": query }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["viewer"]["guid"], "viewer:{}".format(self.authenticatedAdminUser.id))
        self.assertEqual(data["viewer"]["loggedIn"], True)
        self.assertEqual(data["viewer"]["isSubEditor"], self.authenticatedAdminUser.has_role(USER_ROLES.EDITOR) or self.authenticatedAdminUser.has_role(USER_ROLES.ADMIN))
        self.assertEqual(data["viewer"]["isAdmin"], self.authenticatedAdminUser.has_role(USER_ROLES.ADMIN))
        self.assertEqual(data["viewer"]["isBanned"], False)
        self.assertEqual(data["viewer"]["user"]["name"], self.authenticatedAdminUser.name)
        self.assertEqual(data["viewer"]["user"]["guid"], self.authenticatedAdminUser.guid)

    def test_viewer_can_write_to_container_anonymous(self):
        query = """
            {
                viewer {
                    canWriteToContainer(subtype: "news")
                }
            }
        """
        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["viewer"]["canWriteToContainer"], False)

    def test_viewer_can_write_to_container_user(self):
        query = """
            {
                viewer {
                    canWriteToContainer(subtype: "news")
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["viewer"]["canWriteToContainer"], False)

        query = """
            {
                viewer {
                    canWriteToContainer(subtype: "blog")
                }
            }
        """

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["viewer"]["canWriteToContainer"], True)

    def test_viewer_can_write_to_container_group_user(self):
        query = """
            {
                viewer {
                    canWriteToContainer(subtype: "news")
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["viewer"]["canWriteToContainer"], False)

    def test_viewer_can_write_to_container_admin(self):
        query = """
            {
                viewer {
                    canWriteToContainer(subtype: "news")
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedAdminUser

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["viewer"]["canWriteToContainer"], True)

    def test_viewer_can_write_to_container_group_nonmember(self):
        query = f"""
            {{
                viewer {{
                    canWriteToContainer(
                        containerGuid: "{self.group.id}"
                        subtype: "blog"
                    )
                }}
            }}
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["viewer"]["canWriteToContainer"], False)

    def test_viewer_can_write_to_container_group_member(self):
        query = f"""
            {{
                viewer {{
                    canWriteToContainer(
                        containerGuid: "{self.group.id}"
                        subtype: "blog"
                    )
                }}
            }}
        """

        request = HttpRequest()
        request.user = self.groupUser

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["viewer"]["canWriteToContainer"], True)

    def test_viewer_can_write_to_container_wiki_group_user(self):
        query = f"""
            {{
                viewer {{
                    canWriteToContainer(
                        containerGuid: "{self.wiki.id}"
                        subtype: "wiki"
                    )
                }}
            }}
        """

        request = HttpRequest()
        request.user = self.groupUser

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["viewer"]["canWriteToContainer"], False)

    def test_viewer_can_write_to_container_wiki_group_owner(self):
        query = f"""
            {{
                viewer {{
                    canWriteToContainer(
                        containerGuid: "{self.wiki.id}"
                        subtype: "wiki"
                    )
                }}
            }}
        """

        request = HttpRequest()
        request.user = self.groupOwner

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["viewer"]["canWriteToContainer"], True)

    def test_viewer_can_write_to_container_wiki_group_admin(self):
        query = f"""
            {{
                viewer {{
                    canWriteToContainer(
                        containerGuid: "{self.wiki.id}"
                        subtype: "wiki"
                    )
                }}
            }}
        """

        request = HttpRequest()
        request.user = self.groupAdmin

        result = graphql_sync(schema, { "query": query}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["viewer"]["canWriteToContainer"], True)
