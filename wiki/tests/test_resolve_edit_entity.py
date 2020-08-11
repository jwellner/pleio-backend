from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from wiki.models import Wiki
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError

class AddWikiCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.wikiPublic = Wiki.objects.create(
            title="Test public wiki",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.data = {
            "input": {
                "guid": self.wikiPublic.guid,
                "title": "My first Wiki",
                "description": "My description",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"]
            }
        }
        self.mutation = """
            fragment WikiParts on Wiki {
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
                isBookmarked
                canBookmark
                inGroup
                group {
                    guid
                }
                hasChildren
                children {
                    guid
                }
                parent {
                    guid
                }
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...WikiParts
                    }
                }
            }
        """

    def test_edit_wiki(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["hasChildren"], False)

        self.wikiPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.wikiPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["description"], self.wikiPublic.description)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.wikiPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["hasChildren"], self.wikiPublic.has_children())
