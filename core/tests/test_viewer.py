from django.db import connection
from django.test import TestCase
from ..models import User
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import User

class ViewerTestCase(TestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = User.objects.create(name="Viewer Test1", email="viewer1@pleio.nl")
        self.authenticatedAdminUser = User.objects.create(name="Viewer Test2", email="viewer2@pleio.nl", is_admin = True)
    
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

        result = graphql_sync(schema, { "query": query }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["viewer"]["guid"], "0")
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

        result = graphql_sync(schema, { "query": query }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["viewer"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["viewer"]["loggedIn"], True)
        self.assertEqual(data["viewer"]["isSubEditor"], False)
        self.assertEqual(data["viewer"]["isAdmin"], False)
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
                    user {
                        guid
                        name
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedAdminUser

        result = graphql_sync(schema, { "query": query }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["viewer"]["guid"], self.authenticatedAdminUser.guid)
        self.assertEqual(data["viewer"]["loggedIn"], True)
        self.assertEqual(data["viewer"]["isSubEditor"], False)
        self.assertEqual(data["viewer"]["isAdmin"], True)
        self.assertEqual(data["viewer"]["user"]["name"], self.authenticatedAdminUser.name)
        self.assertEqual(data["viewer"]["user"]["guid"], self.authenticatedAdminUser.guid)