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

class BookmarkTestCase(FastTenantTestCase):

    def setUp(self):        
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.blog1 = Blog.objects.create(
            title="Test1",
            description="Description",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True
        )

        self.blog2 = Blog.objects.create(
            title="Test2",
            description="Description",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True
        )

        self.bookmark1 = self.blog1.add_bookmark(self.authenticatedUser)
        self.bookmark2 = self.blog2.add_bookmark(self.authenticatedUser)


    def tearDown(self):
        self.bookmark1.delete()
        self.bookmark2.delete()
        self.blog1.delete()
        self.blog2.delete()
        self.authenticatedUser.delete()
    
    def test_bookmark_list(self):

        query = """
            {
                bookmarks {
                    total
                    canWrite
                    edges {
                        guid
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["bookmarks"]["total"], 2)
        self.assertEqual(data["bookmarks"]["edges"][0]["guid"], self.bookmark2.content_object.guid)

    def test_bookmark_list_filter(self):

        query = """
            {
                bookmarks(subtype: "news") {
                    total
                    canWrite
                    edges {
                        guid
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {}

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["bookmarks"]["total"], 0)

    def test_bookmark(self):

        query = """
            mutation ($bookmark: bookmarkInput!) {
                bookmark(input: $bookmark) {
                    object {
                        guid
                    }
                }
            }
        """

        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "bookmark": {
                "guid": self.blog1.guid,
                "isAdding": False
            }
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["bookmark"]["object"]["guid"], self.blog1.guid)

        query = """
            {
                bookmarks {
                    total
                    canWrite
                    edges {
                        guid
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {}

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["bookmarks"]["total"], 1)
        self.assertEqual(data["bookmarks"]["edges"][0]["guid"], self.blog2.guid)