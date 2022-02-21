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
                        tags
                    }
                }
            }
        """
        variables = {}

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["groups"]["total"], 0)
        self.assertEqual(data["groups"]["edges"], [])

class GroupsNotEmptyTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.group1 = mixer.blend(Group, tags=["tag_one"])
        self.group1.join(self.user, 'member')
        self.groups = mixer.cycle(5).blend(Group, is_closed=False)
        self.group2 = mixer.blend(Group, is_featured=True)

    def tearDown(self):
        for group in self.groups:
            group.delete()
        self.group1.delete()
        self.group2.delete()
        self.user.delete()

    def test_groups_default(self):

        query = """
            {
                groups {
                    total
                    edges {
                        guid
                        name
                        tags
                    }
                }
            }
        """
        variables = {}

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["groups"]["total"], 7)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group2.guid)

    def test_groups_limit(self):

        query = """
            {
                groups(limit:1) {
                    total
                    edges {
                        guid
                        name
                        tags
                    }
                }
            }
        """
        variables = {}

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["groups"]["total"], 7)

    def test_groups_mine(self):

        query = """
            query GroupsQuery($filter: GroupFilter, $offset: Int!, $limit: Int!, $q: String!) {
                groups(filter: $filter, offset: $offset, limit: $limit, q: $q) {
                    total
                    edges {
                        guid
                        name
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

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group1.guid)

    def test_groups_filtered_on_tag(self):

        query = """
            query GroupsQuery($tags: [String], $offset: Int!, $limit: Int!, $q: String!) {
                groups(tags: $tags, offset: $offset, limit: $limit, q: $q) {
                    total
                    edges {
                        guid
                        name
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
            "tags": ["tag_one"],
            "offset": 0,
            "limit": 20,
            "q": ""
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group1.guid)


class HiddenGroupTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymous_user = AnonymousUser()
        self.authenticated_user = mixer.blend(User, name="yy")
        self.group_member_user = mixer.blend(User, name="xx")
        self.non_member_user = mixer.blend(User, name="yyy")
        self.group = mixer.blend(Group, owner=self.authenticated_user,
                                 introduction='introductionMessage',
                                 is_hidden=True)
        self.group.join(self.group_member_user, 'member')

    def test_hidden_group_is_hidden_for_non_members(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
               }
            }
        """

        request = HttpRequest()
        request.user = self.non_member_user

        result = graphql_sync(schema, {"query": query}, context_value={"request": request})
        self.assertTrue(result[0])
        self.assertEqual(result[1]["data"]["groups"]["total"], 0)

    def test_hidden_group_is_visible_for_members(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
                    edges {      
                        guid
                    }    
               }
            }
        """

        request = HttpRequest()
        request.user = self.group_member_user

        result = graphql_sync(schema, {"query": query}, context_value={"request": request})

        self.assertTrue(result[0])
        data = result[1]["data"]
        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group.guid)

    def test_hidden_group_is_hidden_for_anonymous_users(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
               }
            }
        """
        request = HttpRequest()
        request.user = self.anonymous_user

        result = graphql_sync(schema, {"query": query}, context_value={"request": request})
        self.assertTrue(result[0])
        self.assertEqual(result[1]["data"]["groups"]["total"], 0)
