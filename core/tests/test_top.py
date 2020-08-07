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

class TopTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)

        self.blog1 = Blog.objects.create(
            title="Test1",
            description="Description 1",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_one", "tag_two", "tag_three", "tag_four", "tag_five"]
        )
        self.blog2 = Blog.objects.create(
            title="Test2",
            description="Description 2",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_two"]
        )
        self.blog3 = Blog.objects.create(
            title="Test3",
            description="Description 3",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_one", "tag_two", "tag_three"]
        )
        self.blog4 = Blog.objects.create(
            title="Test4",
            description="Description 4",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_one", "tag_two"]
        )

        self.blog5 = Blog.objects.create(
            title="Test5",
            description="Description 5",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_three", "tag_two"]
        )

        self.blog6 = Blog.objects.create(
            title="Test6",
            description="Description 6",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user3.id)],
            owner=self.user3,
            tags=["tag_three", "tag_two"]
        )

        self.blog1.add_vote(user=self.user1, score=1)
        self.blog2.add_vote(user=self.user1, score=1)
        self.blog3.add_vote(user=self.user1, score=1)
        self.blog4.add_vote(user=self.user1, score=1)
        self.blog5.add_vote(user=self.user1, score=1)
        self.blog5.add_vote(user=self.user2, score=1)
        self.blog6.add_vote(user=self.user2, score=1)
        self.blog3.delete()


    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.blog4.delete()
        self.blog5.delete()
        self.blog6.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

    def test_top(self):

        query = """
            query Top {
                top {
                    user {
                    guid
                    username
                    url
                    name
                    icon
                    __typename
                    }
                    likes
                    __typename
                }
            }
        """

        request = HttpRequest()
        request.user = self.user2

        variables = {}

        result = graphql_sync(schema, {"query": query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(len(data["top"]), 2)
        self.assertEqual(data["top"][0]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["top"][0]["likes"], 5)
        self.assertEqual(data["top"][1]["user"]["guid"], self.user3.guid)
        self.assertEqual(data["top"][1]["likes"], 1)


# votes > entities, gebruikers met meeste votes