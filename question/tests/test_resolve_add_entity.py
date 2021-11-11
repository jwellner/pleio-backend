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

class AddQuestionTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.data = {
            "input": {
                "type": "object",
                "subtype": "question",
                "title": "My first Question",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True,
                "featured": {
                    "positionY": 10,
                    "video": "testVideo",
                    "videoTitle": "testVideoTitle",
                    "alt": "testAlt"
                }
            }
        }
        self.mutation = """
            fragment QuestionParts on Question {
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
                isClosed
                isFeatured
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...QuestionParts
                    }
                }
            }
        """

    def test_add_question(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["addEntity"]["entity"]["isClosed"], False)
        self.assertEqual(data["addEntity"]["entity"]["isFeatured"], False) # only with editor or admin role
        self.assertEqual(data["addEntity"]["entity"]["featured"]["positionY"], 10)
        self.assertEqual(data["addEntity"]["entity"]["featured"]["video"], "testVideo")
        self.assertEqual(data["addEntity"]["entity"]["featured"]["videoTitle"], "testVideoTitle")
        self.assertEqual(data["addEntity"]["entity"]["featured"]["alt"], "testAlt")

    def test_add_question_to_group(self):

        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["inGroup"], True)
        self.assertEqual(data["addEntity"]["entity"]["group"]["guid"], self.group.guid)
