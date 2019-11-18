from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import User, Group
from file.models import FileFolder
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class EntityTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser)
        self.file = FileFolder.objects.create(
            owner=self.authenticatedUser, 
            upload=None, 
            is_folder=False, 
            parent=None, 
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

    def tearDown(self):
        self.group.delete()
        self.file.delete()
        self.authenticatedUser.delete()
    

    def test_entity_user_anonymous(self):

        query = """
            query getUser($username: String!) {
                entity(username: $username) {
                    guid
                    status
                    __typename
                }
            }
        """
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = { 
            "username": self.authenticatedUser.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertIsNone(data["entity"])

    def test_entity_user_by_username(self):

        query = """
            query getUser($username: String!) {
                entity(username: $username) {
                    guid
                    status
                    __typename
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "username": self.authenticatedUser.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["entity"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["entity"]["__typename"], "User")

    def test_entity_user_by_guid(self):

        query = """
            query getUser($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    __typename
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "guid": self.authenticatedUser.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["entity"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["entity"]["__typename"], "User")

    def test_entity_group(self):

        query = """
            query getGroup($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    __typename
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "guid": self.group.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["__typename"], "Group")

    def test_entity_file_folder(self):

        query = """
            query getFileFolder($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    __typename
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "guid": self.file.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["entity"]["guid"], self.file.guid)
        self.assertEqual(data["entity"]["__typename"], "FileFolder")

