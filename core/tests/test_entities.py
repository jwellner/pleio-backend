from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import User, Group
from blog.models import Blog
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class EntityTestCase(FastTenantTestCase):

    def setUp(self):
        self.authenticatedUser = mixer.blend(User)
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

        self.query = """
            query getEntities($containerGuid: String, $tags: [String!]) {
                entities(containerGuid: $containerGuid, tags: $tags) {
                    total
                    edges {
                        guid
                        __typename
                    }
                }
            }
        """

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.blog3.delete()
        self.group.delete()
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

        self.assertEqual(data["entities"]["total"], 3)

    def test_entities_site(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "containerGuid": "1"
        }

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entities"]["total"], 2)

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
