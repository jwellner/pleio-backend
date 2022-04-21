from django.db import connection
from core.models.attachment import Attachment
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
from django.utils import timezone

class AddEventTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.eventPublic = mixer.blend(Event, 
            owner=self.authenticatedUser, 
            read_access=[ACCESS_TYPE.public], 
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)]
        )

        self.eventGroupPublic = mixer.blend(Event, 
            owner=self.authenticatedUser, 
            read_access=[ACCESS_TYPE.public], 
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            group=self.group
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
                "locationLink": "maps.google.nl",
                "locationAddress": "Kerkstraat 10",
                "source": "https://www.pleio.nl",
                "ticketLink": "https://www.pleio.nl",
                "attendEventWithoutAccount": True,
                "rsvp": True
            }
        }
        self.mutation = """
            fragment EventParts on Event {
                title
                richDescription
                parent {
                    guid
                }
                hasChildren
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
                ticketLink
                attendEventWithoutAccount
                startDate
                endDate
                location
                locationLink
                locationAddress
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
        self.assertEqual(data["addEntity"]["entity"]["locationLink"], variables["input"]["locationLink"])
        self.assertEqual(data["addEntity"]["entity"]["locationAddress"], variables["input"]["locationAddress"])
        self.assertEqual(data["addEntity"]["entity"]["rsvp"], variables["input"]["rsvp"])
        self.assertEqual(data["addEntity"]["entity"]["source"], variables["input"]["source"])
        self.assertEqual(data["addEntity"]["entity"]["ticketLink"], variables["input"]["ticketLink"])
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

    def test_add_event_with_attachment(self):
        attachment = mixer.blend(Attachment)

        variables = self.data
        variables["input"]["richDescription"] = json.dumps({ 'type': 'file', 'attrs': {'url': f"/attachment/entity/{attachment.id}" }})

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": self.mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]
        event = Event.objects.get(id=data["addEntity"]["entity"]["guid"])

        self.assertTrue(event.attachments.filter(id=attachment.id).exists())