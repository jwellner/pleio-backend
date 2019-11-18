from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone
from core.models import User, Group
from ..models import Task
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify


class TaskTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.taskPublic = Task.objects.create(
            title="Test public event",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            state="NEW"
        )

        self.taskPrivate = Task.objects.create(
            title="Test private event",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            state="NEW"
        )

        self.query = """
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
            query GetTask($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...TaskParts
                }
            }
        """

    def tearDown(self):
        self.taskPublic.delete()
        self.taskPrivate.delete()
        self.authenticatedUser.delete()

    def test_task_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.taskPublic.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.taskPublic.guid)
        self.assertEqual(data["entity"]["title"], self.taskPublic.title)
        self.assertEqual(data["entity"]["description"], self.taskPublic.description)
        self.assertEqual(data["entity"]["richDescription"], self.taskPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], str(self.taskPublic.created_at))
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["url"], "/task/view/{}/{}".format(self.taskPublic.guid, slugify(self.taskPublic.title)))
        self.assertEqual(data["entity"]["state"], self.taskPublic.state)

        variables = {
            "guid": self.taskPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

    def test_task_private(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.taskPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value=request)

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.taskPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.taskPrivate.title)
        self.assertEqual(data["entity"]["description"], self.taskPrivate.description)
        self.assertEqual(data["entity"]["richDescription"], self.taskPrivate.rich_description)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.taskPrivate.created_at))
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["state"], self.taskPrivate.state)
