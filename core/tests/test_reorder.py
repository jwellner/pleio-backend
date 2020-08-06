from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from cms.models import Page
from wiki.models import Wiki

class ReorderTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.admin = mixer.blend(User, is_admin=True)      

        self.page1 = mixer.blend(Page,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.page2 = mixer.blend(Page,
                                 position=0,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)],
                                 parent=self.page1
                                 )
        self.page3 = mixer.blend(Page,
                                 position=1,
                                 parent=self.page1,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.page4 = mixer.blend(Page,
                                 position=2,
                                 parent=self.page1,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.page5 = mixer.blend(Page,
                                 position=3,
                                 parent=self.page1,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.page6 = mixer.blend(Page,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        # when no position is set order is created_at (OLD -> NEW)
        self.page7 = mixer.blend(Page,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)],
                                 parent=self.page6
                                 )
        self.page8 = mixer.blend(Page,
                                 parent=self.page6,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.page9 = mixer.blend(Page,
                                 parent=self.page6,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )         
        self.wiki1 = mixer.blend(Wiki,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.wiki2 = mixer.blend(Wiki,
                                 position=0,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)],
                                 parent=self.wiki1
                                 )
        self.wiki3 = mixer.blend(Wiki,
                                 position=1,
                                 parent=self.wiki1,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.wiki4 = mixer.blend(Wiki,
                                 position=2,
                                 parent=self.wiki1,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.wiki5 = mixer.blend(Wiki,
                                 position=3,
                                 parent=self.wiki1,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.wiki6 = mixer.blend(Wiki,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        # when no position is set order is created_at (OLD -> NEW)
        self.wiki7 = mixer.blend(Wiki,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)],
                                 parent=self.wiki6
                                 )
        self.wiki8 = mixer.blend(Wiki,
                                 parent=self.wiki6,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )
        self.wiki9 = mixer.blend(Wiki,
                                 parent=self.wiki6,
                                 owner=self.user,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.user.id)]
                                 )         

    def tearDown(self):
        self.wiki9.delete()
        self.wiki8.delete()
        self.wiki7.delete()
        self.wiki5.delete()
        self.wiki4.delete()
        self.wiki3.delete()
        self.wiki2.delete()
        self.wiki1.delete()
        self.wiki6.delete()
        self.page9.delete()
        self.page8.delete()
        self.page7.delete()
        self.page5.delete()
        self.page4.delete()
        self.page3.delete()
        self.page2.delete()
        self.page1.delete()
        self.page6.delete()

    def test_reorder_page_move_up_position_by_admin(self):

        mutation = """
            mutation SubNavReorder($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Page {
                                children {
                                    guid
                                    title
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
            "input": {
                "guid": self.page2.guid,
                "sourcePosition": 0,
                "destinationPosition": 2
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(Page.objects.get(id=self.page2.id).position, 2)
        self.assertEqual(Page.objects.get(id=self.page3.id).position, 0)
        self.assertEqual(Page.objects.get(id=self.page4.id).position, 1)
        self.assertEqual(Page.objects.get(id=self.page5.id).position, 3)
        self.assertEqual(data["reorder"]["container"]["children"][0]["guid"], self.page3.guid)
        self.assertEqual(data["reorder"]["container"]["children"][1]["guid"], self.page4.guid)


    def test_reorder_page_move_up_position_by_owner(self):

        mutation = """
            mutation SubNavReorder($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Page {
                                children {
                                    guid
                                    title
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
            "input": {
                "guid": self.page2.guid,
                "sourcePosition": 0,
                "destinationPosition": 2
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_reorder_page_move_down_position_by_admin(self):

        mutation = """
            mutation SubNavReorder($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Page {
                                children {
                                    guid
                                    title
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
            "input": {
                "guid": self.page4.guid,
                "sourcePosition": 2,
                "destinationPosition": 0
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(Page.objects.get(id=self.page4.id).position, 0)
        self.assertEqual(Page.objects.get(id=self.page2.id).position, 1)
        self.assertEqual(Page.objects.get(id=self.page3.id).position, 2)
        self.assertEqual(Page.objects.get(id=self.page5.id).position, 3)
        self.assertEqual(data["reorder"]["container"]["children"][0]["guid"], self.page4.guid)
        self.assertEqual(data["reorder"]["container"]["children"][1]["guid"], self.page2.guid)


    def test_reorder_page_move_up_position_unordered_children_by_admin(self):

        # default order is OLD -> NEW when no position is set

        mutation = """
            mutation SubNavReorder($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Page {
                                children {
                                    guid
                                    title
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
            "input": {
                "guid": self.page8.guid,
                "sourcePosition": 1,
                "destinationPosition": 2
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(Page.objects.get(id=self.page7.id).position, 0)
        self.assertEqual(Page.objects.get(id=self.page8.id).position, 2)
        self.assertEqual(Page.objects.get(id=self.page9.id).position, 1)
        self.assertEqual(data["reorder"]["container"]["children"][0]["guid"], self.page7.guid)
        self.assertEqual(data["reorder"]["container"]["children"][1]["guid"], self.page9.guid)

    def test_reorder_page_move_down_position_unordered_children_by_admin(self):

        # default order is OLD -> NEW when no position is set

        mutation = """
            mutation SubNavReorder($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Page {
                                children {
                                    guid
                                    title
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
            "input": {
                "guid": self.page8.guid,
                "sourcePosition": 1,
                "destinationPosition": 0
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(Page.objects.get(id=self.page7.id).position, 1)
        self.assertEqual(Page.objects.get(id=self.page8.id).position, 0)
        self.assertEqual(Page.objects.get(id=self.page9.id).position, 2)
        self.assertEqual(data["reorder"]["container"]["children"][0]["guid"], self.page8.guid)
        self.assertEqual(data["reorder"]["container"]["children"][1]["guid"], self.page7.guid)

    def test_reorder_wiki_move_up_position_by_admin(self):

        mutation = """
            mutation WikiNavMutation($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Wiki {
                                canEdit
                                title
                                url
                                parent {
                                title
                                url
                                __typename
                            }
                            children {
                                guid
                                title
                                url
                                canEdit
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
            "input": {
                "guid": self.wiki2.guid,
                "sourcePosition": 0,
                "destinationPosition": 2
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(Wiki.objects.get(id=self.wiki2.id).position, 2)
        self.assertEqual(Wiki.objects.get(id=self.wiki3.id).position, 0)
        self.assertEqual(Wiki.objects.get(id=self.wiki4.id).position, 1)
        self.assertEqual(Wiki.objects.get(id=self.wiki5.id).position, 3)
        self.assertEqual(data["reorder"]["container"]["children"][0]["guid"], self.wiki3.guid)
        self.assertEqual(data["reorder"]["container"]["children"][1]["guid"], self.wiki4.guid)


    def test_reorder_wiki_move_down_position_by_admin(self):

        mutation = """
            mutation WikiNavMutation($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Wiki {
                                canEdit
                                title
                                url
                                parent {
                                title
                                url
                                __typename
                            }
                            children {
                                guid
                                title
                                url
                                canEdit
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
            "input": {
                "guid": self.wiki4.guid,
                "sourcePosition": 2,
                "destinationPosition": 0
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(Wiki.objects.get(id=self.wiki4.id).position, 0)
        self.assertEqual(Wiki.objects.get(id=self.wiki2.id).position, 1)
        self.assertEqual(Wiki.objects.get(id=self.wiki3.id).position, 2)
        self.assertEqual(Wiki.objects.get(id=self.wiki5.id).position, 3)
        self.assertEqual(data["reorder"]["container"]["children"][0]["guid"], self.wiki4.guid)
        self.assertEqual(data["reorder"]["container"]["children"][1]["guid"], self.wiki2.guid)


    def test_reorder_wiki_move_up_position_unordered_children_by_admin(self):

        # default order is OLD -> NEW when no position is set

        mutation = """
            mutation WikiNavMutation($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Wiki {
                                canEdit
                                title
                                url
                                parent {
                                title
                                url
                                __typename
                            }
                            children {
                                guid
                                title
                                url
                                canEdit
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
            "input": {
                "guid": self.wiki8.guid,
                "sourcePosition": 1,
                "destinationPosition": 2
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(Wiki.objects.get(id=self.wiki7.id).position, 0)
        self.assertEqual(Wiki.objects.get(id=self.wiki8.id).position, 2)
        self.assertEqual(Wiki.objects.get(id=self.wiki9.id).position, 1)
        self.assertEqual(data["reorder"]["container"]["children"][0]["guid"], self.wiki7.guid)
        self.assertEqual(data["reorder"]["container"]["children"][1]["guid"], self.wiki9.guid)


    def test_reorder_wiki_move_down_position_unordered_children_by_admin(self):

        # default order is OLD -> NEW when no position is set

        mutation = """
            mutation WikiNavMutation($input: reorderInput!) {
                reorder(input: $input) {
                    container {
                        guid
                        ... on Wiki {
                                canEdit
                                title
                                url
                                parent {
                                title
                                url
                                __typename
                            }
                            children {
                                guid
                                title
                                url
                                canEdit
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
            "input": {
                "guid": self.wiki8.guid,
                "sourcePosition": 1,
                "destinationPosition": 0
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, {"query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(Wiki.objects.get(id=self.wiki7.id).position, 1)
        self.assertEqual(Wiki.objects.get(id=self.wiki8.id).position, 0)
        self.assertEqual(Wiki.objects.get(id=self.wiki9.id).position, 2)
        self.assertEqual(data["reorder"]["container"]["children"][0]["guid"], self.wiki8.guid)
        self.assertEqual(data["reorder"]["container"]["children"][1]["guid"], self.wiki7.guid)