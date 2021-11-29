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
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class EditStatusUpdateTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.group = mixer.blend(Group)

        self.statusPublic = StatusUpdate.objects.create(
            title="Test public update",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.data = {
            "input": {
                "guid": self.statusPublic.guid,
                "title": "My first update",
                "richDescription": "richDescription",
                "tags": ["tag1", "tag2"],
            }
        }
        self.mutation = """
            fragment StatusUpdateParts on StatusUpdate {
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

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])

        self.statusPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.statusPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.statusPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["group"], None)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], self.statusPublic.created_at.isoformat())


    def test_edit_status_update_by_admin(self):

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
        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.user2.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], "2018-12-10T23:00:00+00:00")


        self.statusPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.statusPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.statusPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["editEntity"]["entity"]["owner"]["guid"], self.user2.guid)
        self.assertEqual(data["editEntity"]["entity"]["timeCreated"], "2018-12-10T23:00:00+00:00")


    def test_edit_status_update_group_null_by_admin(self):

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
