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
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from unittest import mock

class AttendEventTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.attendee1 = mixer.blend(User, email="attendee1@example.net")
        self.attendee2 = mixer.blend(User, email="attendee2@example.net")
        self.attendee3 = mixer.blend(User, email="attendee3@example.net")
        self.attendee4 = mixer.blend(User, email="attendee4@example.net")
        self.attendee5 = mixer.blend(User, email="attendee5@example.net")
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
                                name
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
                                name
                                email
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

        guids = [r['guid'] for r in data["attendEvent"]["entity"]["attendees"]["edges"]]
        emails = [r['email'] for r in data["attendEvent"]["entity"]["attendees"]["edges"]]

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 1)
        self.assertNotIn(str(self.attendee3.id), guids)
        self.assertIn(str(self.attendee2.id), guids)
        self.assertEqual([''], emails)


    def test_attend_event_from_accept_to_reject(self):
        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "accept") {
                            edges {
                                name
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

    def test_not_attending_parent_event(self):

        subevent = Event.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.attendee1.id)],
            owner=self.attendee1,
            max_attendees = 2,
            parent=self.eventPublic
        )

        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "accept") {
                            edges {
                                name
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
                "guid": subevent.guid,
                "state": 'accept'
            }
        }

        request = HttpRequest()
        request.user = self.attendee2

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_attending_parent_event")

    def test_reject_event_with_subevent(self):
        subevent = mixer.blend(
            Event,
            parent = self.eventPublic,
        )

        sub_attendee = mixer.blend(
            EventAttendee,
            event = subevent,
            user = self.attendee1,
            state = 'accept'
        )

        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "reject") {
                            edges {
                                name
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
                "state": 'reject'
            }
        }

        request = HttpRequest()
        request.user = self.attendee1

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        sub_attendee.refresh_from_db()

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 1)
        self.assertEqual(sub_attendee.state, 'reject')

    def test_maybe_event_with_subevent(self):
        subevent = mixer.blend(
            Event,
            parent = self.eventPublic,
        )

        sub_attendee = mixer.blend(
            EventAttendee,
            event = subevent,
            user = self.attendee1,
            state = 'accept'
        )

        mutation = """
            mutation AttendEvent($input: attendEventInput!) {
                attendEvent(input: $input) {
                    entity {
                        guid
                        attendees(state: "maybe") {
                            edges {
                                name
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

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        sub_attendee.refresh_from_db()

        self.assertEqual(data["attendEvent"]["entity"]["guid"], self.eventPublic.guid)
        self.assertEqual(len(data["attendEvent"]["entity"]["attendees"]["edges"]), 1)
        self.assertEqual(sub_attendee.state, 'maybe')