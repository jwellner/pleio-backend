from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from ..models import StatusUpdate
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class EditStatusUpdateTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.statusPublic = StatusUpdate.objects.create(
            title="Test public update",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.data = {
            "input": {
                "guid": self.statusPublic.guid,
                "title": "My first update",
                "description": "My description",
                "richDescription": "richDescription",
                "tags": ["tag1", "tag2"],
            }
        }
        self.mutation = """
            fragment StatusUpdateParts on StatusUpdate {
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
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...StatusUpdateParts
                    }
                }
            }
        """

    def test_edit_status_update(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])

        self.statusPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.statusPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["description"], self.statusPublic.description)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.statusPublic.rich_description)
