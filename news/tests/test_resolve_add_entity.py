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
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class AddNewsTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.adminUser = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.editorUser = mixer.blend(User, roles=[USER_ROLES.EDITOR])

        self.data = {
            "input": {
                "type": "object",
                "subtype": "news",
                "title": "My first News",
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
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...NewsParts
                    }
                }
            }
        """

    def test_add_news(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["addEntity"], None)

    def test_add_news_admin(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.adminUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["addEntity"]["entity"]["isFeatured"], True)
        self.assertEqual(data["addEntity"]["entity"]["source"], variables["input"]["source"])

    def test_add_news_editor(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.editorUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["addEntity"]["entity"]["isFeatured"], True)
        self.assertEqual(data["addEntity"]["entity"]["source"], variables["input"]["source"])
