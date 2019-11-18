from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from mixer.backend.django import mixer

class GroupsEmptyTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()

    def test_groups_empty(self):

        query = """
            {
                groups {
                    total
                    canWrite
                    edges {
                        guid
                        name
                        description
                        tags
                    }
                }
            }
        """
        variables = {}

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["groups"]["total"], 0)
        self.assertEqual(data["groups"]["canWrite"], False)
        self.assertEqual(data["groups"]["edges"], [])

class GroupsNotEmptyTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.groups = mixer.cycle(5).blend(Group, is_closed=False)
  
    def tearDown(self):
        for group in self.groups:
            group.delete()
        self.user.delete()

    def test_groups_default(self):

        query = """
            {
                groups {
                    total
                    canWrite
                    edges {
                        guid
                        name
                        description
                        tags
                    }
                }
            }
        """
        variables = {}

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["groups"]["total"], 5)
        self.assertEqual(data["groups"]["canWrite"], False)

    def test_groups_limit(self):

        query = """
            {
                groups(limit:2) {
                    total
                    canWrite
                    edges {
                        guid
                        name
                        description
                        tags
                    }
                }
            }
        """
        variables = {}

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        
        self.assertEqual(data["groups"]["total"], 2)
        self.assertEqual(data["groups"]["canWrite"], False)

