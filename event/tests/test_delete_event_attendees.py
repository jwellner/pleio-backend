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
from event.models import Event, EventAttendee, EventAttendeeRequest
from event.lib import get_url
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime
from unittest import mock

class DeleteEventAttendeesTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.eventOwner = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()
        self.event = mixer.blend(Event)
        self.event.owner = self.eventOwner
        self.event.read_access = [ACCESS_TYPE.public]
        self.event.write_access=[ACCESS_TYPE.user.format(self.eventOwner.id)]
        self.event.attend_event_without_account = True
        self.event.save()

        EventAttendee.objects.create(
            event=self.event,
            user=self.authenticatedUser,
            email=None
        )
        EventAttendee.objects.create(
            event=self.event,
            user=None,
            email="test1@test.nl"
        )
        EventAttendee.objects.create(
            event=self.event,
            user=None,
            email="test2@test.nl"
        )

    def tearDown(self):
        self.event.delete()
        self.authenticatedUser.delete()
        self.eventOwner.delete()

    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi.delay')
    def test_delete_attendees_from_event_by_admin(self, mocked_send_mail_multi):
        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.authenticatedUser.email]
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]
        
        self.event.refresh_from_db()

        self.assertEqual(self.event.attendees.count(), 1)
        self.assertEqual(data["deleteEventAttendees"]["entity"]["guid"], self.event.guid)
        self.assertEqual(mocked_send_mail_multi.call_count, 2)


    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi.delay')
    def test_delete_attendees_from_event_by_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.authenticatedUser.email]
            }
        }

        request = HttpRequest()
        request.user = self.eventOwner

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]
        
        self.event.refresh_from_db()

        self.assertEqual(self.event.attendees.count(), 1)
        self.assertEqual(data["deleteEventAttendees"]["entity"]["guid"], self.event.guid)
        self.assertEqual(mocked_send_mail_multi.call_count, 2)

    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi.delay')
    def test_delete_attendees_from_event_by_user(self, mocked_send_mail_multi):
        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.authenticatedUser.email]
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")

    def test_delete_attendees_from_event_with_subevent(self):
        subevent = mixer.blend(Event,
            parent = self.event
        )

        mixer.blend(EventAttendee, 
            user = self.authenticatedUser,
            event = subevent
        )

        self.assertEqual(subevent.attendees.count(), 1)

        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.authenticatedUser.email]
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]
        
        self.event.refresh_from_db()

        self.assertEqual(self.event.attendees.count(), 1)
        self.assertEqual(data["deleteEventAttendees"]["entity"]["guid"], self.event.guid)
        self.assertEqual(subevent.attendees.count(), 0)

    def test_delete_attendees_from_event(self):
        subevent = mixer.blend(Event,
            parent = self.event
        )

        EventAttendee.objects.create(
            event=subevent,
            user=None
        )

        self.assertEqual(subevent.attendees.count(), 1)

        mutation = """
            mutation deleteEventAttendees($input: deleteEventAttendeesInput!) {
                deleteEventAttendees(input: $input) {
                    entity {
                        guid
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddresses": ["test2@test.nl", self.authenticatedUser.email]
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]
        
        self.event.refresh_from_db()

        self.assertEqual(self.event.attendees.count(), 1)
        self.assertEqual(data["deleteEventAttendees"]["entity"]["guid"], self.event.guid)
        self.assertEqual(subevent.attendees.count(), 1)