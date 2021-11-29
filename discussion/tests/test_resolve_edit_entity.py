from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from ..models import Discussion
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class EditDiscussionTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.group = mixer.blend(Group)

        self.discussionPublic = Discussion.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=False
        )

        self.data = {
            "input": {
                "guid": self.discussionPublic.guid,
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True,
                "featured": {
                    "positionY": 2,
                    "video": "testVideo2",
                    "videoTitle": "testVideoTitle2",
                    "alt": "testAlt2"
                }
            }
        }

        self.mutation = """
            fragment DiscussionParts on Discussion {
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
                featured {
                    image
                    video
                    videoTitle
                    positionY
                    alt
                }
                group {
                    guid
                }
                owner {
                    guid
                }
                isFeatured
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...DiscussionParts
                    }
                }
            }
        """

    def test_edit_discussion(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["isFeatured"], False)

        self.discussionPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.discussionPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.discussionPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["isFeatured"], False)
        self.assertEqual(data["editEntity"]["entity"]["group"], None)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], self.discussionPublic.created_at.isoformat())
        self.assertEqual(data["editEntity"]["entity"]["featured"]["positionY"], 2)
        self.assertEqual(data["editEntity"]["entity"]["featured"]["video"], "testVideo2")
        self.assertEqual(data["editEntity"]["entity"]["featured"]["videoTitle"], "testVideoTitle2")
        self.assertEqual(data["editEntity"]["entity"]["featured"]["alt"], "testAlt2")


    def test_edit_discussion_by_admin(self):

        variables = self.data
        variables["input"]["timeCreated"] = "2018-12-10T23:00:00.000Z"
        variables["input"]["groupGuid"] = self.group.guid
        variables["input"]["ownerGuid"] = self.user2.guid

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["isFeatured"], True)
        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.user2.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], "2018-12-10T23:00:00+00:00")

        self.discussionPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.discussionPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.discussionPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["isFeatured"], True)
        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.user2.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], "2018-12-10T23:00:00+00:00")


    def test_edit_discussion_group_null_by_admin(self):

        variables = self.data
        variables["input"]["groupGuid"] = self.group.guid

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)

        variables["input"]["groupGuid"] = None

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["group"], None)
