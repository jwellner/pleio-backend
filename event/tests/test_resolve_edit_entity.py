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
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime

class EditEventTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.eventPublic = Event.objects.create(
            title="Test public event",
            description="Description",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            start_date=datetime.now()
        )

        self.data = {
            "input": {
                "guid": self.eventPublic.guid,
                "title": "My first Event",
                "description": "My description",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "startDate": "2019-10-02 09:38:33.976000",
                "endDate": "2019-10-02 09:38:33.976000",
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
                rsvp
                source
                attendEventWithoutAccount
                startDate
                endDate
                location
                maxAttendees
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...EventParts
                    }
                }
            }
        """

    def test_edit_event(self):

        variables = self.data

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], variables["input"]["title"])
        self.assertEqual(data["editEntity"]["entity"]["description"], variables["input"]["description"])
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(data["editEntity"]["entity"]["startDate"], variables["input"]["startDate"])
        self.assertEqual(data["editEntity"]["entity"]["endDate"], variables["input"]["endDate"])
        self.assertEqual(data["editEntity"]["entity"]["maxAttendees"], variables["input"]["maxAttendees"])
        self.assertEqual(data["editEntity"]["entity"]["location"], variables["input"]["location"])
        self.assertEqual(data["editEntity"]["entity"]["source"], variables["input"]["source"])
        self.assertEqual(data["editEntity"]["entity"]["attendEventWithoutAccount"], variables["input"]["attendEventWithoutAccount"])
        self.assertEqual(data["editEntity"]["entity"]["rsvp"], variables["input"]["rsvp"])

        self.eventPublic.refresh_from_db()

        self.assertEqual(data["editEntity"]["entity"]["title"], self.eventPublic.title)
        self.assertEqual(data["editEntity"]["entity"]["description"], self.eventPublic.description)
        self.assertEqual(data["editEntity"]["entity"]["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(data["editEntity"]["entity"]["startDate"], str(self.eventPublic.start_date))
        self.assertEqual(data["editEntity"]["entity"]["endDate"], str(self.eventPublic.end_date))
        self.assertEqual(data["editEntity"]["entity"]["maxAttendees"], str(self.eventPublic.max_attendees))
        self.assertEqual(data["editEntity"]["entity"]["location"], self.eventPublic.location)
        self.assertEqual(data["editEntity"]["entity"]["source"], self.eventPublic.external_link)
        self.assertEqual(data["editEntity"]["entity"]["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)
        self.assertEqual(data["editEntity"]["entity"]["rsvp"], self.eventPublic.rsvp)
