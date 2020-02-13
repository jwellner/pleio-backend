from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group
from user.models import User
from blog.models import Blog
from cms.models import Page
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class EntitiesTestCase(FastTenantTestCase):

    def setUp(self):
        self.authenticatedUser = mixer.blend(User)
        self.admin = mixer.blend(User, is_admin=True)
        self.group = mixer.blend(Group, owner=self.authenticatedUser)
        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            tags=["tag_one"]
        )
        self.blog3 = Blog.objects.create(
            title="Blog3",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            group=self.group,
            tags=["tag_two", "tag_one"]
        )
        self.page1 = mixer.blend(Page,
                                 owner=self.admin,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.admin.id)]
                                 )
        self.page2 = mixer.blend(Page,
                                 position=0,
                                 owner=self.admin,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.admin.id)],
                                 parent=self.page1
                                 )
        self.page3 = mixer.blend(Page,
                                 position=1,
                                 parent=self.page1,
                                 owner=self.admin,
                                 read_access=[ACCESS_TYPE.public],
                                 write_access=[ACCESS_TYPE.user.format(self.admin.id)]
                                 )

        self.query = """
            query getEntities($subtype: String, $containerGuid: String, $tags: [String!]) {
                entities(subtype: $subtype, containerGuid: $containerGuid, tags: $tags) {
                    total
                    edges {
                        guid
                        __typename
                    }
                }
            }
        """

    def tearDown(self):
        self.page1.delete()
        self.page2.delete()
        self.page3.delete()
        self.blog1.delete()
        self.blog2.delete()
        self.blog3.delete()
        self.group.delete()
        self.admin.delete()
        self.authenticatedUser.delete()

    def test_entities_all(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": None
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 6)

    def test_entities_site(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": "1"
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 5)

    def test_entities_group(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": self.group.guid
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 1)

    def test_entities_filtered_by_tags_find_one(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"tags": ["tag_two"]}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 1)
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)

    def test_entities_filtered_by_tags_find_two(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"tags": ["tag_one"]}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 2)
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)
        self.assertEqual(data["entities"]["edges"][1]["guid"], self.blog2.guid)


    def test_entities_filtered_by_tags_find_one_with_two_tags(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {"tags": ["tag_one", "tag_two"]}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["entities"]["total"], 1)
        self.assertEqual(data["entities"]["edges"][0]["guid"], self.blog3.guid)


    def test_entities_all_pages_by_admin(self):
        request = HttpRequest()
        request.user = self.admin

        variables = {
            "subtype": "page"
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"] 

        self.assertEqual(data["entities"]["total"], 1)
