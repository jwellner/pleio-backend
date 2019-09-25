from django.db import connection
from django.test import TestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import User, Group
from wiki.models import Wiki
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl
from core.resolvers.shared import access_id_to_acl
from django.utils.text import slugify

class WikiTestCase(TestCase):

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

        self.wikiPrivate = Wiki.objects.create(
            title="Test private wiki",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            parent=self.wikiPublic
        )

        self.query = """
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
            query GetWiki($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...WikiParts
                }
            }
        """

    def tearDown(self):
        self.wikiPublic.delete()
        self.wikiPrivate.delete()
        self.authenticatedUser.delete()

    def test_news_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.wikiPublic.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.wikiPublic.guid)
        self.assertEqual(data["entity"]["title"], self.wikiPublic.title)
        self.assertEqual(data["entity"]["description"], self.wikiPublic.description)
        self.assertEqual(data["entity"]["richDescription"], self.wikiPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], str(self.wikiPublic.created_at))
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["canBookmark"], False)
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["url"], "/wiki/view/{}/{}".format(self.wikiPublic.guid, slugify(self.wikiPublic.title)))
        self.assertEqual(data["entity"]["parent"], None)
        self.assertEqual(data["entity"]["hasChildren"], True)
        self.assertEqual(data["entity"]["children"][0]["guid"], self.wikiPrivate.guid)

        variables = {
            "guid": self.wikiPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

    def test_news_private(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.wikiPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.wikiPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.wikiPrivate.title)
        self.assertEqual(data["entity"]["description"], self.wikiPrivate.description)
        self.assertEqual(data["entity"]["richDescription"], self.wikiPrivate.rich_description)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.wikiPrivate.created_at))
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["canBookmark"], True)
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["url"], "/wiki/view/{}/{}".format(self.wikiPrivate.guid, slugify(self.wikiPrivate.title)))
        self.assertEqual(data["entity"]["parent"]['guid'], self.wikiPublic.guid)
