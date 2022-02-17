from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from django.utils.text import slugify
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group
from user.models import User
from event.models import Event, EventAttendee
from event.lib import get_url
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from unittest import mock

class AttendEventTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.attendee1 = mixer.blend(User)
        self.attendee2 = mixer.blend(User)
        self.attendee3 = mixer.blend(User)
        self.attendee4 = mixer.blend(User)
        self.attendee5 = mixer.blend(User)
        self.eventPublic = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.attendee1.id)],
            owner=self.attendee1,
            max_attendees = 2
        )
        mixer.blend(
            EventAttendee,
            user=self.attendee1,
            event=self.eventPublic,
            state='accept'
        )

    def tearDown(self):
        self.eventPublic.delete()
        self.attendee1.delete()
        self.attendee2.delete()
        self.attendee3.delete()

    def test_attend_event_accept(self):
        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "accept") {
                            edges {
                                guid
                            }
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.eventPublic.guid,
                "state": 'accept'
            }
        }

        request = HttpRequest()
        request.user = self.attendee2

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 2)


    def test_attend_event_waitinglist(self):
        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "waitinglist") {
                            edges {
                                guid
                            }
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.eventPublic.guid,
                "state": 'waitinglist'
            }
        }

        request = HttpRequest()
        request.user = self.attendee2

        mixer.blend(
            EventAttendee,
            user=self.attendee3,
            event=self.eventPublic,
            state='accept'
        )

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 1)
        self.assertEqual(data["attendEvent"]["entity"]["attendees"]["edges"][0]["guid"], self.attendee2.guid)


    def test_attend_event_from_accept_to_reject(self):
        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "accept") {
                            edges {
                                guid
                            }
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.eventPublic.guid,
                "state": 'maybe'
            }
        }

        request = HttpRequest()
        request.user = self.attendee1

        mixer.blend(
            EventAttendee,
            user=self.attendee2,
            event=self.eventPublic,
            state='accept'
        )
        mixer.blend(
            EventAttendee,
            user=self.attendee3,
            event=self.eventPublic,
            state='waitinglist'
        )
        mixer.blend(
            EventAttendee,
            user=self.attendee4,
            event=self.eventPublic,
            state='waitinglist'
        )
        mixer.blend(
            EventAttendee,
            user=self.attendee5,
            event=self.eventPublic,
            state='waitinglist'
        )

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 2)
        self.assertEqual(EventAttendee.objects.filter(event=self.eventPublic, user=self.attendee3, state='accept').count(), 1)