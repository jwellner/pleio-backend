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

class VoteTestCase(FastTenantTestCase):

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

    def tearDown(self):
        self.blog1.delete()
        self.authenticatedUser.delete()
    
    def test_bookmark(self):

        query = """
            mutation ($input: voteInput!) {
                vote(input: $input) {
                    object {
                        guid
                    }
                }
            }
        """

        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "input": {
                "guid": self.blog1.guid,
                "score": 1
            }
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["vote"]["object"]["guid"], self.blog1.guid)
        self.assertEqual(self.blog1.vote_count(), 1)

        # Test "unvote"
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "score": -1
            }
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["vote"]["object"]["guid"], self.blog1.guid)
        self.assertEqual(self.blog1.vote_count(), 0)

        # Test "down-vote"
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "score": -1
            }
        }

        result = graphql_sync(schema, { "query": query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]
       
        self.assertEqual(data["vote"]["object"]["guid"], self.blog1.guid)
        self.assertEqual(self.blog1.vote_count(), -1)