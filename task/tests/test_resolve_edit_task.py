from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from ..models import Task
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class EditTaskTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.group = mixer.blend(Group)

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
                owner {
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

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["state"], "NEW")
        self.assertEqual(data["editEntity"]["entity"]["group"], None)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], str(self.taskPublic.created_at))

        self.taskPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.taskPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["description"], self.taskPublic.description)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.taskPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["state"], self.taskPublic.state)


    def test_edit_task_by_admin(self):

        variables = self.data
        variables["input"]["timeCreated"] = "2018-12-10T23:00:00.000Z"
        variables["input"]["groupGuid"] = self.group.guid
        variables["input"]["ownerGuid"] = self.user2.guid

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["state"], "NEW")
        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.user2.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], "2018-12-10 23:00:00+00:00")

        self.taskPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.taskPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["description"], self.taskPublic.description)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.taskPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["state"], self.taskPublic.state)
        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.user2.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], "2018-12-10 23:00:00+00:00")


    def test_edit_task_group_null_by_admin(self):

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
