from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, Subgroup
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from graphql import GraphQLError
from core.constances import ACCESS_TYPE

class SubgroupsTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.admin = mixer.blend(User, is_admin=True)
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User, name='test_na')
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User)
        self.user5 = mixer.blend(User)
        self.user6 = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.user1)
        self.group.join(self.user1, 'owner')
        self.group.join(self.user2, 'member')
        self.group.join(self.user3, 'member')
        self.group.join(self.user4, 'member')
        self.group.join(self.user5, 'member')
        self.group.join(self.user6, 'member')

        self.subgroup1 = Subgroup.objects.create(
            name='testSubgroup1',
            group=self.group,
            id=1
        )
        self.subgroup1.members.add(self.user2)
        self.subgroup1.members.add(self.user3)
        self.subgroup1.members.add(self.user6)

        self.group.leave(self.user6)

        self.blog = Blog.objects.create(
            title="Test subgroup blog",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.user1.id), ACCESS_TYPE.subgroup.format(self.subgroup1.access_id)],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            group=self.group,
            is_recommended=False
        )


    def tearDown(self):
        self.blog.delete()
        self.subgroup1.delete()
        self.group.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.user4.delete()
        self.user5.delete()
        self.user6.delete()
        self.admin.delete()

    def test_query_subgroups_by_group_owner(self):

        query = """
            query SubgroupsList($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        guid
                        subgroups {
                            total
                            edges {
                            id
                            name
                            members {
                                guid
                                __typename
                            }
                            __typename
                            }
                            __typename
                        }
                        __typename
                        }
                    __typename
                }
            }
        """
        variables = {"guid": self.group.guid}

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["subgroups"]["total"], 1)
        self.assertEqual(data["entity"]["subgroups"]["edges"][0]["id"], self.subgroup1.id)
        self.assertEqual(data["entity"]["subgroups"]["edges"][0]["name"], self.subgroup1.name)

    def test_query_subgroups_memberlist_by_group_owner(self):

        query = """
            query SubgroupMembersList($guid: String!, $subgroupId: Int, $q: String, $offsetInSubgroup: Int, $offsetNotInSubgroup: Int) {
                inSubgroup: entity(guid: $guid) {
                    ... on Group {
                        guid
                        canEdit
                        canChangeOwnership
                        members(q: $q, offset: $offsetInSubgroup, limit: 20, inSubgroupId: $subgroupId) {
                            total
                            edges {
                                role
                                email
                                user {
                                    guid
                                    username
                                    url
                                    name
                                    icon
                                    __typename
                                }
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
                notInSubgroup: entity(guid: $guid) {
                    ... on Group {
                        guid
                        canEdit
                        canChangeOwnership
                        members(q: $q, offset: $offsetNotInSubgroup, limit: 20, notInSubgroupId: $subgroupId) {
                            total
                            edges {
                                role
                                email
                                user {
                                    guid
                                    username
                                    url
                                    name
                                    icon
                                    __typename
                                }
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "guid": self.group.guid,
            "subgroupId": self.subgroup1.id,
            "q": ""
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["inSubgroup"]["guid"], self.group.guid)
        self.assertEqual(data["inSubgroup"]["members"]["total"], 2)
        self.assertEqual(data["notInSubgroup"]["guid"], self.group.guid)
        self.assertEqual(data["notInSubgroup"]["members"]["total"], 3)


    def test_query_subgroup_access_fields(self):
        query = """
            query AccessField($guid: String) {
                entity(guid: $guid) {
                    guid
                    status
                    ... on Group {
                        defaultAccessId
                        accessIds {
                            id
                            description
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {"guid": self.group.guid}

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["defaultAccessId"], 1)
        self.assertEqual(data["entity"]["accessIds"][2]["id"], 10001)


    def test_blog_in_subgroup_by_subgroup_member(self):

        query = """
            fragment BlogParts on Blog {
                title
                accessId
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """
        request = HttpRequest()
        request.user = self.user2

        variables = { 
            "guid": self.blog.guid
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["entity"]["guid"], self.blog.guid)
        self.assertEqual(data["entity"]["accessId"], 10001)

    def test_blog_in_subgroup_by_non_subgroup_member(self):

        query = """
            fragment BlogParts on Blog {
                title
                accessId
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """
        request = HttpRequest()
        request.user = self.user5

        variables = { 
            "guid": self.blog.guid
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_find")


    def test_blog_in_subgroup_by_subgroup_member_which_left_group(self):

        query = """
            fragment BlogParts on Blog {
                title
                accessId
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """
        request = HttpRequest()
        request.user = self.user6

        variables = { 
            "guid": self.blog.guid
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_find")


    def test_query_subgroups_memberlist_with_filter(self):

        query = """
            query SubgroupMembersList($guid: String!, $subgroupId: Int, $q: String, $offsetInSubgroup: Int, $offsetNotInSubgroup: Int) {
                inSubgroup: entity(guid: $guid) {
                    ... on Group {
                        guid
                        canEdit
                        canChangeOwnership
                        members(q: $q, offset: $offsetInSubgroup, limit: 20, inSubgroupId: $subgroupId) {
                            total
                            edges {
                                role
                                email
                                user {
                                    guid
                                    username
                                    url
                                    name
                                    icon
                                    __typename
                                }
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
                notInSubgroup: entity(guid: $guid) {
                    ... on Group {
                        guid
                        canEdit
                        canChangeOwnership
                        members(q: $q, offset: $offsetNotInSubgroup, limit: 20, notInSubgroupId: $subgroupId) {
                            total
                            edges {
                                role
                                email
                                user {
                                    guid
                                    username
                                    url
                                    name
                                    icon
                                    __typename
                                }
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "guid": self.group.guid,
            "subgroupId": self.subgroup1.id,
            "q": "test_na"
        }

        request = HttpRequest()
        request.user = self.user1

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["inSubgroup"]["guid"], self.group.guid)
        self.assertEqual(data["inSubgroup"]["members"]["total"], 1)
        self.assertEqual(data["notInSubgroup"]["guid"], self.group.guid)
        self.assertEqual(data["notInSubgroup"]["members"]["total"], 0)
