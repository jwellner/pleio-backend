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
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify

class NewsTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.newsPublic = News.objects.create(
            title="Test public news",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=True,
            source="source1"
        )

        self.newsPrivate = News.objects.create(
            title="Test private news",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=False,
            source="source2"
        )

        self.query = """
            fragment NewsParts on News {
                title
                description
                richDescription
                accessId
                timeCreated
                featured {
                    image
                    video
                    positionY
                }
                isFeatured
                canEdit
                tags
                url
                views
                votes
                hasVoted
                isBookmarked
                isFollowing
                canBookmark
                owner {
                    guid
                }
                source
            }
            query GetNews($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...NewsParts
                }
            }
        """

    def tearDown(self):
        self.newsPublic.delete()
        self.newsPrivate.delete()
        self.authenticatedUser.delete()
    
    def test_news_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = { 
            "guid": self.newsPublic.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["entity"]["guid"], self.newsPublic.guid)
        self.assertEqual(data["entity"]["title"], self.newsPublic.title)
        self.assertEqual(data["entity"]["description"], self.newsPublic.description)
        self.assertEqual(data["entity"]["richDescription"], self.newsPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], str(self.newsPublic.created_at))
        self.assertEqual(data["entity"]["isFeatured"], self.newsPublic.is_featured)
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["views"], 1)
        self.assertEqual(data["entity"]["votes"], 0)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["isFollowing"], False)
        self.assertEqual(data["entity"]["canBookmark"], False)
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["owner"]["guid"], self.newsPublic.owner.guid)
        self.assertEqual(data["entity"]["url"], "/news/view/{}/{}".format(self.newsPublic.guid, slugify(self.newsPublic.title)))
        self.assertEqual(data["entity"]["source"], self.newsPublic.source)

        variables = { 
            "guid": self.newsPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["entity"], None)

    def test_news_private(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = { 
            "guid": self.newsPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["entity"]["guid"], self.newsPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.newsPrivate.title)
        self.assertEqual(data["entity"]["description"], self.newsPrivate.description)
        self.assertEqual(data["entity"]["richDescription"], self.newsPrivate.rich_description)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.newsPrivate.created_at))
        self.assertEqual(data["entity"]["isFeatured"], self.newsPrivate.is_featured)
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["views"], 1)
        self.assertEqual(data["entity"]["votes"], 0)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["isFollowing"], False)
        self.assertEqual(data["entity"]["canBookmark"], True)
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["owner"]["guid"], self.newsPrivate.owner.guid)
        self.assertEqual(data["entity"]["url"], "/news/view/{}/{}".format(self.newsPrivate.guid, slugify(self.newsPrivate.title)))
        self.assertEqual(data["entity"]["source"], self.newsPrivate.source)
