from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from event.models import Event
from core.constances import ACCESS_TYPE
from core.lib import datetime_isoformat
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import timezone

class AddEventTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.eventPublic = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            start_date=timezone.now()
        )

        self.eventGroupPublic = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            group=self.group,
            start_date=timezone.now()
        )

        self.data = {
            "input": {
                "type": "object",
                "subtype": "event",
                "title": "My first Event",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "startDate": "2019-10-02T09:00:00+02:00",
                "endDate": "2019-10-02T10:00:00+02:00",
                "maxAttendees": "10",
                "location": "Utrecht",
                "source": "https://www.pleio.nl",
                "attendEventWithoutAccount": True,
                "rsvp": True
            }
        }
        self.mutation = """
            fragment EventParts on Event {
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
                rsvp
                source
                attendEventWithoutAccount
                startDate
                endDate
                location
                maxAttendees
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...EventParts
                    }
                }
            }
        """

    def test_add_event(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["location"], variables["input"]["location"])
        self.assertEqual(data["addEntity"]["entity"]["rsvp"], variables["input"]["rsvp"])
        self.assertEqual(data["addEntity"]["entity"]["source"], variables["input"]["source"])
        self.assertEqual(data["addEntity"]["entity"]["startDate"], "2019-10-02T09:00:00+02:00")
        self.assertEqual(data["addEntity"]["entity"]["endDate"], "2019-10-02T10:00:00+02:00")
        self.assertEqual(data["addEntity"]["entity"]["attendEventWithoutAccount"], variables["input"]["attendEventWithoutAccount"])
        self.assertEqual(data["addEntity"]["entity"]["maxAttendees"], variables["input"]["maxAttendees"])

    def test_add_event_to_group(self):

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

    def test_add_event_to_parent(self):

        variables = self.data
        variables["input"]["containerGuid"] = self.eventPublic.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["hasChildren"], False)
        self.assertEqual(data["addEntity"]["entity"]["parent"]["guid"], self.eventPublic.guid)

        self.eventPublic.refresh_from_db()

        self.assertTrue(self.eventPublic.has_children())
        self.assertEqual(self.eventPublic.children.first().guid, data["addEntity"]["entity"]["guid"])


    def test_add_event_to_parent_with_group(self):

        variables = self.data
        variables["input"]["containerGuid"] = self.eventGroupPublic.guid

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["addEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["addEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["addEntity"]["entity"]["hasChildren"], False)
        self.assertEqual(data["addEntity"]["entity"]["inGroup"], True)
        self.assertEqual(data["addEntity"]["entity"]["group"]["guid"], self.group.guid)
        self.assertEqual(data["addEntity"]["entity"]["parent"]["guid"], self.eventGroupPublic.guid)

        self.eventGroupPublic.refresh_from_db()

        self.assertTrue(self.eventGroupPublic.has_children())
        self.assertEqual(self.eventGroupPublic.children.first().guid, data["addEntity"]["entity"]["guid"])
