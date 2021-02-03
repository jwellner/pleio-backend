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
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify

class BlogTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedAdminUser = mixer.blend(User, roles = ['ADMIN'])

        self.blogPublic = Blog.objects.create(
            title="Test public blog",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True
        )

        self.blogPrivate = Blog.objects.create(
            title="Test private blog",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=False
        )

    def tearDown(self):
        self.blogPublic.delete()
        self.blogPrivate.delete()
        self.authenticatedUser.delete()
        self.authenticatedAdminUser.delete()

    def test_blog_anonymous(self):

        query = """
            fragment BlogParts on Blog {
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
                isRecommended
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
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.blogPublic.guid
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.blogPublic.guid)
        self.assertEqual(data["entity"]["title"], self.blogPublic.title)
        self.assertEqual(data["entity"]["description"], self.blogPublic.description)
        self.assertEqual(data["entity"]["richDescription"], self.blogPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], str(self.blogPublic.created_at))
        self.assertEqual(data["entity"]["isRecommended"], self.blogPublic.is_recommended)
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["views"], 1)
        self.assertEqual(data["entity"]["votes"], 0)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["isBookmarked"], False)
        self.assertEqual(data["entity"]["isFollowing"], False)
        self.assertEqual(data["entity"]["canBookmark"], False)
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["owner"]["guid"], self.blogPublic.owner.guid)
        self.assertEqual(data["entity"]["url"], "/blog/view/{}/{}".format(self.blogPublic.guid, slugify(self.blogPublic.title)))

        variables = {
            "guid": self.blogPrivate.guid
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)
