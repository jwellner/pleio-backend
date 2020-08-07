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
                "description": "My description",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"]
            }
        }
        self.mutation = """
            fragment QuestionParts on Question {
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
                inGroup
                group {
                    guid
                }
                isClosed
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

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["tags"], variables["input"]["tags"])
        self.assertEqual(data["addEntity"]["entity"]["isClosed"], False)

    def test_add_question_to_group(self):

        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["inGroup"], True)
        self.assertEqual(data["addEntity"]["entity"]["group"]["guid"], self.group.guid)
