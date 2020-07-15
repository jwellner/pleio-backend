from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from news.models import News
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class EditBlogTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.news = News.objects.create(
            title="Test public news",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=False
        )

        self.data = {
            "input": {
                "guid": self.news.guid,
                "title": "My first News item",
                "description": "My description",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True,
                "source": "https://www.nos.nl"
            }
        }
        self.mutation = """
            fragment NewsParts on News {
                title
                description
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                url
                isFeatured
                source
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...NewsParts
                    }
                }
            }
        """

    def test_edit_news(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["editEntity"]["entity"]["isFeatured"], variables["input"]["isFeatured"])
        self.assertEqual(data["editEntity"]["entity"]["source"], variables["input"]["source"])

        self.news.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.news.title)
        self.assertEqual(data["editEntity"]["entity"]["description"], self.news.description)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.news.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["tags"], self.news.tags)
        self.assertEqual(data["editEntity"]["entity"]["isFeatured"], self.news.is_featured)
        self.assertEqual(data["editEntity"]["entity"]["source"], self.news.source)
