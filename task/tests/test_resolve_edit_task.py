from django.db import connection
from django.test import TestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, User
from ..models import Task
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class EditTaskTestCase(TestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.taskPublic = Task.objects.create(
            title="Test public update",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.data = {
            "input": {
                "guid": self.taskPublic.guid,
                "title": "My first update",
                "description": "My description",
                "richDescription": "richDescription",
            }
        }
        self.mutation = """
            fragment TaskParts on Task {
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
                state
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...TaskParts
                    }
                }
            }
        """

    def test_edit_task(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["state"], "NEW")

        self.taskPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.taskPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["description"], self.taskPublic.description)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.taskPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["state"], self.taskPublic.state)
