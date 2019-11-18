from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import User, Group
from blog.models import Blog
from news.models import News
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class RecommendedTestCase(FastTenantTestCase):

    def setUp(self):
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            is_recommended=True
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
        )
        self.news1 = News.objects.create(
            title="News1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
        )
        self.query = """
            query Recommended {
                recommended(limit: 3) {
                    total
                    edges {
                    guid
                    ... on Blog {
                        title
                        subtype
                        url
                        owner {
                        guid
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
            }
        """

    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.news1.delete()
        self.user2.delete()
        self.user1.delete()

    def test_recommended(self):
        request = HttpRequest()
        request.user = self.user1

        variables = {}

        result = graphql_sync(schema, { "query": self.query, "variables": variables }, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["recommended"]["total"], 1)
        self.assertEqual(data["recommended"]["edges"][0]["guid"], self.blog1.guid)
