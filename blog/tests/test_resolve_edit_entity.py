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
from django.utils import dateparse

class EditBlogTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)

        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()

        self.group = mixer.blend(Group)
        self.blog = Blog.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=False
        )

    def tearDown(self):
        self.blog.delete()
        self.authenticatedUser.delete()
        self.user2.delete()
        self.admin.delete()
        self.group.delete()



    def test_edit_blog(self):




        variables = {
            "input": {
                "guid": self.blog.guid,
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True,
                "timeCreated": "2018-12-10T23:00:00.000Z",
                "groupGuid": self.group.guid,
                "ownerGuid": self.user2.guid,
                "timePublished": None
            }
        }

        mutation = """
            fragment BlogParts on Blog {
                title
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                timePublished
                statusPublished
                url
                inGroup
                group {
                    guid
                }
                owner {
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


        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["editEntity"]["entity"]["isRecommended"], False) # only admin can set isRecommended
        self.assertEqual(data["editEntity"]["entity"]["group"], None)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], str(self.blog.created_at))
        self.assertEqual(data["editEntity"]["entity"]["statusPublished"], 'draft')
        self.assertEqual(data["editEntity"]["entity"]["timePublished"], None)

        self.blog.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.blog.title)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.blog.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["tags"], self.blog.tags)
        self.assertEqual(data["editEntity"]["entity"]["isRecommended"], self.blog.is_recommended)


    def test_edit_blog_by_admin(self):


        variables = {
            "input": {
                "guid": self.blog.guid,
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True,
                "timeCreated": "2018-12-10T23:00:00.000Z",
                "groupGuid": self.group.guid,
                "ownerGuid": self.user2.guid
            }
        }

        mutation = """
            fragment BlogParts on Blog {
                title
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                statusPublished
                group {
                    guid
                }
                owner {
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

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["editEntity"]["entity"]["isRecommended"], True)
        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.user2.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], "2018-12-10 23:00:00+00:00")

        self.blog.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.blog.title)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.blog.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["tags"], self.blog.tags)
        self.assertEqual(data["editEntity"]["entity"]["isRecommended"], self.blog.is_recommended)
        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.user2.guid)
        self.assertEqual(data["editEntity"]["entity"]["statusPublished"], "published")
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], "2018-12-10 23:00:00+00:00")

    def test_edit_blog_group_null_by_admin(self):

        variables = {
            "input": {
                "guid": self.blog.guid,
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True,
                "timeCreated": "2018-12-10T23:00:00.000Z",
                "groupGuid": self.group.guid,
                "ownerGuid": self.user2.guid
            }
        }

        mutation = """
            fragment BlogParts on Blog {
                title
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
                owner {
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

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)


        variables["input"]["groupGuid"] = None
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["group"], None)


    def test_edit_blog_set_future_published(self):

        variables = {
            "input": {
                "guid": self.blog.guid,
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isRecommended": True,
                "timeCreated": "2018-12-10T23:00:00.000Z",
                "groupGuid": self.group.guid,
                "ownerGuid": self.user2.guid,
                "timePublished": "4018-12-10T23:00:00.000Z"
            }
        }

        mutation = """
            fragment BlogParts on Blog {
                title
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                timePublished
                statusPublished
                url
                inGroup
                group {
                    guid
                }
                owner {
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


        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["editEntity"]["entity"]["isRecommended"], False) # only admin can set isRecommended
        self.assertEqual(data["editEntity"]["entity"]["group"], None)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], str(self.blog.created_at))
        self.assertEqual(data["editEntity"]["entity"]["statusPublished"], 'draft')
        self.assertEqual(data["editEntity"]["entity"]["timePublished"], "4018-12-10 23:00:00+00:00")

        self.blog.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.blog.title)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.blog.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["tags"], self.blog.tags)
        self.assertEqual(data["editEntity"]["entity"]["isRecommended"], self.blog.is_recommended)
