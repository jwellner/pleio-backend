from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from mixer.backend.django import mixer

class GroupsEmptyTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()

    def test_groups_empty(self):

        query = """
            {
                groups {
                    total
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
        self.assertEqual(data["groups"]["edges"], [])

class GroupsNotEmptyTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.group1 = mixer.blend(Group)
        self.group1.join(self.user, 'member')
        self.groups = mixer.cycle(5).blend(Group, is_closed=False)
  
    def tearDown(self):
        for group in self.groups:
            group.delete()
        self.group1.delete()
        self.user.delete()

    def test_groups_default(self):

        query = """
            {
                groups {
                    total
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
        
        self.assertEqual(data["groups"]["total"], 6)

    def test_groups_limit(self):

        query = """
            {
                groups(limit:2) {
                    total
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

    def test_groups_mine(self):

        query = """
            query GroupsQuery($filter: GroupFilter, $offset: Int!, $limit: Int!, $q: String!) {
                groups(filter: $filter, offset: $offset, limit: $limit, q: $q) {
                    total
                    edges {
                        guid
                        name
                        description
                        richDescription
                        canEdit
                        excerpt
                        isMembershipOnRequest
                        isClosed
                        isFeatured
                        membership
                        members {
                            total
                            __typename
                        }
                        icon
                        url
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "filter": "mine",
            "offset": 0,
            "limit": 20,
            "q": ""
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group1.guid)
