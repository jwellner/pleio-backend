from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone
from core.models import Group
from user.models import User
from event.models import Event, EventAttendee
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl, datetime_isoformat
from django.utils.text import slugify


class EventTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User, name="test_name2")
        self.user = mixer.blend(User)
        self.user2 = mixer.blend(User, name="test_name3")

        self.eventPublic = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            start_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None
        )

        self.eventPrivate = Event.objects.create(
            title="Test private event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            start_date=timezone.now(),
            end_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=100,
            attend_event_without_account=True
        )

        EventAttendee.objects.create(
            event=self.eventPrivate,
            state='accept',
            user=self.user2
        )

        EventAttendee.objects.create(
            event=self.eventPrivate,
            state='accept',
            name="test_name4",
            email='test@test4.nl'
        )

        EventAttendee.objects.create(
            event=self.eventPrivate,
            state='accept',
            name="test_name",
            email='test@test.nl'
        )

        EventAttendee.objects.create(
            event=self.eventPrivate,
            state='accept',
            user=self.authenticatedUser
        )

        EventAttendee.objects.create(
            event=self.eventPublic,
            state='accept',
            name="test_name",
            email='test@test.nl'
        )

        self.query = """
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
                startDate
                endDate
                location
                source
                rsvp
                location
                attendEventWithoutAccount
                attendees {
                    total
                    edges {
                        name
                        email
                        url
                        icon
                        state
                    }
                }
            }
            query GetEvent($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...EventParts
                }
            }
        """

    def tearDown(self):
        self.eventPublic.delete()
        self.eventPrivate.delete()
        self.authenticatedUser.delete()

    def test_event_anonymous(self):

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.eventPublic.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })
        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(data["entity"]["title"], self.eventPublic.title)
        self.assertEqual(data["entity"]["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], self.eventPublic.created_at.isoformat())
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["url"], "/events/view/{}/{}".format(self.eventPublic.guid, slugify(self.eventPublic.title)))
        self.assertEqual(data["entity"]["startDate"], str(datetime_isoformat(self.eventPublic.start_date)))
        self.assertEqual(data["entity"]["endDate"], None)
        self.assertEqual(data["entity"]["source"], self.eventPublic.external_link)
        self.assertEqual(data["entity"]["location"], self.eventPublic.location)
        self.assertEqual(data["entity"]["rsvp"], self.eventPublic.rsvp)
        self.assertEqual(data["entity"]["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)
        self.assertEqual(len(data["entity"]["attendees"]["edges"]), 0)

        variables = {
            "guid": self.eventPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

    def test_event_private(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.eventPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.eventPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.eventPrivate.title)
        self.assertEqual(data["entity"]["richDescription"], self.eventPrivate.rich_description)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], self.eventPrivate.created_at.isoformat())
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["url"], "/events/view/{}/{}".format(self.eventPrivate.guid, slugify(self.eventPrivate.title)))
        self.assertEqual(data["entity"]["startDate"], str(datetime_isoformat(self.eventPrivate.start_date)))
        self.assertEqual(data["entity"]["endDate"], str(datetime_isoformat(self.eventPrivate.end_date)))
        self.assertEqual(data["entity"]["source"], self.eventPrivate.external_link)
        self.assertEqual(data["entity"]["location"], self.eventPrivate.location)
        self.assertEqual(data["entity"]["rsvp"], self.eventPrivate.rsvp)
        self.assertEqual(data["entity"]["attendEventWithoutAccount"], self.eventPrivate.attend_event_without_account)
        self.assertEqual(data["entity"]["attendees"]["edges"][2]["name"], 'test_name')
        self.assertEqual(data["entity"]["attendees"]["edges"][2]["url"], None)
        self.assertEqual(data["entity"]["attendees"]["edges"][2]["icon"], None)
        self.assertEqual(data["entity"]["attendees"]["edges"][2]["state"], 'accept')
        self.assertEqual(data["entity"]["attendees"]["edges"][0]["name"], 'test_name2')
        self.assertEqual(data["entity"]["attendees"]["edges"][0]["url"], self.authenticatedUser.url)
        self.assertEqual(data["entity"]["attendees"]["edges"][0]["icon"], self.authenticatedUser.icon)
        self.assertEqual(data["entity"]["attendees"]["edges"][0]["state"], 'accept')
        self.assertEqual(len(data["entity"]["attendees"]["edges"]), 4)

    def test_event_user(self):

        request = HttpRequest()
        request.user = self.user

        variables = {
            "guid": self.eventPublic.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(data["entity"]["title"], self.eventPublic.title)
        self.assertEqual(data["entity"]["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], self.eventPublic.created_at.isoformat())
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["url"], "/events/view/{}/{}".format(self.eventPublic.guid, slugify(self.eventPublic.title)))
        self.assertEqual(data["entity"]["startDate"], str(datetime_isoformat(self.eventPublic.start_date)))
        self.assertEqual(data["entity"]["endDate"], None)
        self.assertEqual(data["entity"]["source"], self.eventPublic.external_link)
        self.assertEqual(data["entity"]["location"], self.eventPublic.location)
        self.assertEqual(data["entity"]["rsvp"], self.eventPublic.rsvp)
        self.assertEqual(data["entity"]["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)
        self.assertEqual(data["entity"]["attendees"]["edges"][0]["name"], "test_name")
        self.assertEqual(data["entity"]["attendees"]["edges"][0]["email"], "")

        variables = {
            "guid": self.eventPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)