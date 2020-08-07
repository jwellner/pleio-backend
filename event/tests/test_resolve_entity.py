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
from event.models import Event
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from core.lib import get_acl, access_id_to_acl
from django.utils.text import slugify


class EventTestCase(FastTenantTestCase):

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
            start_date=timezone.now(),
            location="Utrecht",
            external_link="https://www.pleio.nl",
            rsvp=True,
            max_attendees=None
        )

        self.eventPrivate = Event.objects.create(
            title="Test private event",
            description="Description",
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

        self.query = """
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
                startDate
                endDate
                location
                source
                rsvp
                attendEventWithoutAccount
                location
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

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(data["entity"]["title"], self.eventPublic.title)
        self.assertEqual(data["entity"]["description"], self.eventPublic.description)
        self.assertEqual(data["entity"]["richDescription"], self.eventPublic.rich_description)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], str(self.eventPublic.created_at))
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["url"], "/events/view/{}/{}".format(self.eventPublic.guid, slugify(self.eventPublic.title)))
        self.assertEqual(data["entity"]["startDate"], str(self.eventPublic.start_date))
        self.assertEqual(data["entity"]["endDate"], None)
        self.assertEqual(data["entity"]["source"], self.eventPublic.external_link)
        self.assertEqual(data["entity"]["location"], self.eventPublic.location)
        self.assertEqual(data["entity"]["rsvp"], self.eventPublic.rsvp)
        self.assertEqual(data["entity"]["attendEventWithoutAccount"], self.eventPublic.attend_event_without_account)

        variables = {
            "guid": self.eventPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

    def test_event_private(self):
        request = HttpRequest()
        request.user = self.authenticatedUser

        variables = {
            "guid": self.eventPrivate.guid
        }

        result = graphql_sync(schema, { "query": self.query , "variables": variables}, context_value={ 'request': request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["guid"], self.eventPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.eventPrivate.title)
        self.assertEqual(data["entity"]["description"], self.eventPrivate.description)
        self.assertEqual(data["entity"]["richDescription"], self.eventPrivate.rich_description)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], str(self.eventPrivate.created_at))
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["url"], "/events/view/{}/{}".format(self.eventPrivate.guid, slugify(self.eventPrivate.title)))
        self.assertEqual(data["entity"]["startDate"], str(self.eventPrivate.start_date))
        self.assertEqual(data["entity"]["endDate"], str(self.eventPrivate.end_date))
        self.assertEqual(data["entity"]["source"], self.eventPrivate.external_link)
        self.assertEqual(data["entity"]["location"], self.eventPrivate.location)
        self.assertEqual(data["entity"]["rsvp"], self.eventPrivate.rsvp)
        self.assertEqual(data["entity"]["attendEventWithoutAccount"], self.eventPrivate.attend_event_without_account)
