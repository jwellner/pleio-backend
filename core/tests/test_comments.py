from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Comment
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify

class CommentTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.blogPublic = Blog.objects.create(
            title="Test public blog",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True,
            group=None
        )

        self.comments = mixer.cycle(5).blend(Comment, is_closed=False, owner=self.authenticatedUser, container=self.blogPublic)

    def tearDown(self):
        self.blogPublic.delete()
        self.authenticatedUser.delete()
    
    def test_blog_anonymous(self):

        query = """
            fragment BlogParts on Blog {
                title
                commentCount
                comments {
                    guid
                    description
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

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["entity"]["guid"], self.blogPublic.guid)
        self.assertEqual(data["entity"]["commentCount"], 5)
        self.assertEqual(data["entity"]["comments"][4]['guid'], self.comments[4].guid)