from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class EditBlogTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.blog = Blog.objects.create(
            title="Test public event",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=False
        )

        self.data = {
            "input": {
                "guid": self.blog.guid,
                "title": "My first Event",
                "description": "My description",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True
            }
        }
        self.mutation = """
            fragment BlogParts on Blog {
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
                inGroup
                group {
                    guid
                }
                isRecommended
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """

    def test_edit_blog(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["editEntity"]["entity"]["isRecommended"], False) # only admin can set isRecommended

        self.blog.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.blog.title)
        self.assertEqual(data["editEntity"]["entity"]["description"], self.blog.description)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.blog.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["tags"], self.blog.tags)
        self.assertEqual(data["editEntity"]["entity"]["isRecommended"], self.blog.is_recommended)
