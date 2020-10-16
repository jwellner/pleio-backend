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
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.wikiPublic = Wiki.objects.create(
            title="Test public wiki",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.wikiGroupPublic = Wiki.objects.create(
            title="Test public wiki",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            group=self.group
        )

        self.data = {
            "input": {
                "type": "object",
                "subtype": "wiki",
                "title": "My first Wiki",
                "description": "My description",
                "richDescription": "richDescription",
                "containerGuid": None,
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True
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
                isFeatured
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...WikiParts
                    }
                }
            }
        """

    def test_add_wiki(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["hasChildren"], False)
        self.assertEqual(data["addEntity"]["entity"]["isFeatured"], False) # nly with editor or admin role

    def test_add_wiki_to_parent(self):

        variables = self.data
        variables["input"]["containerGuid"] = self.wikiPublic.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["hasChildren"], False)
        self.assertEqual(data["addEntity"]["entity"]["parent"]["guid"], self.wikiPublic.guid)

        self.wikiPublic.refresh_from_db()

        self.assertTrue(self.wikiPublic.has_children())
        self.assertEqual(self.wikiPublic.children.first().guid, data["addEntity"]["entity"]["guid"])

    def test_add_wiki_to_group(self):

        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["hasChildren"], False)
        self.assertEqual(data["addEntity"]["entity"]["parent"], None)
        self.assertEqual(data["addEntity"]["entity"]["inGroup"], True)
        self.assertEqual(data["addEntity"]["entity"]["group"]["guid"], self.group.guid)

    def test_add_wiki_to_parent_with_group(self):

        variables = self.data
        variables["input"]["containerGuid"] = self.wikiGroupPublic.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["hasChildren"], False)
        self.assertEqual(data["addEntity"]["entity"]["inGroup"], True)
        self.assertEqual(data["addEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["addEntity"]["entity"]["parent"]["guid"], self.wikiGroupPublic.guid)

        self.wikiGroupPublic.refresh_from_db()

        self.assertTrue(self.wikiGroupPublic.has_children())
        self.assertEqual(self.wikiGroupPublic.children.first().guid, data["addEntity"]["entity"]["guid"])
