from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import User, EntityView, EntityViewCount
from blog.models import Blog
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class EntityViewTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)]
        )

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.user1.delete()
        self.user2.delete()

    def test_entity_view_blog(self):

        query = """
            query BlogItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    ...BlogDetailFragment
                    __typename
                }
            }
            fragment BlogDetailFragment on Blog {
                views
            }
        """

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.blog1.guid
        }

        graphql_sync(schema, {"query": query, "variables": variables }, context_value=request)
        graphql_sync(schema, {"query": query, "variables": variables }, context_value=request)
        graphql_sync(schema, {"query": query, "variables": variables }, context_value=request)

        result = graphql_sync(schema, {"query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.blog1.guid)
        self.assertEqual(data["entity"]["views"], 4)

        request = HttpRequest()
        request.user = self.user1

        graphql_sync(schema, {"query": query, "variables": variables }, context_value=request)
        graphql_sync(schema, {"query": query, "variables": variables }, context_value=request)

        result = graphql_sync(schema, {"query": query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["views"], 7)
