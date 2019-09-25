from django.db import connection
from django.test import TestCase
from core.models import User, Group
from blog.models import Blog
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class EntityTestCase(TestCase):

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
        )
        self.blog3 = Blog.objects.create(
            title="Blog3",
            owner=self.authenticatedUser,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            group=self.group
        )

        self.query = """
            query getEntities($containerGuid: String) {
                entities(containerGuid: $containerGuid) {
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