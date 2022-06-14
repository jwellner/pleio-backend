from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from django.utils.text import slugify
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone
from core.models import Group
from user.models import User
from event.models import Event, EventAttendee, EventAttendeeRequest
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime
from unittest import mock

class EditEventAttendeeTestCase(FastTenantTestCase):

    def setUp(self):
        self.today = timezone.now()
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

        self.attendee1 = EventAttendee.objects.create(
            event=self.event,
            user=self.authenticatedUser,
            email=self.authenticatedUser.email,
            checked_in_at=self.today
        )
        self.attendee2 = EventAttendee.objects.create(
            event=self.event,
            user=None,
            email="test1@test.nl",
            
        )
        self.attendee3 = EventAttendee.objects.create(
            event=self.event,
            user=None,
            email="test2@test.nl"
        )

    def tearDown(self):
        self.attendee1.delete()
        self.attendee2.delete()
        self.attendee3.delete()
        self.event.delete()
        self.authenticatedUser.delete()
        self.eventOwner.delete()



    def test_edit_attendee_from_event_by_admin(self):
        mutation = """
            mutation editEventAttendee($input: editEventAttendeeInput!) {
                editEventAttendee(input: $input) {
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
                "emailAddress": "test2@test.nl",
                "timeCheckedIn": self.today.isoformat()
            }
        }

        request = HttpRequest()
        request.user = self.admin

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]
        
        self.attendee3.refresh_from_db()

        self.assertEqual(self.attendee3.checked_in_at, self.today)
        self.assertEqual(self.attendee3.email, "test2@test.nl")
        self.assertEqual(self.attendee3.event, self.event)

    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi.delay')
    def test_edit_attendee_by_event_owner(self, mocked_send_mail_multi):
        mutation = """
            mutation editEventAttendee($input: editEventAttendeeInput!) {
                editEventAttendee(input: $input) {
                    entity {
                        guid
                        attendees {
                            edges {
                                email
                                timeCheckedIn
                            }
                        }
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddress": self.authenticatedUser.email,
                "timeCheckedIn": None
            }
        }

        request = HttpRequest()
        request.user = self.eventOwner

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.attendee1.refresh_from_db()

        self.assertEqual(self.attendee1.checked_in_at, None)
        self.assertEqual(self.attendee1.user.email, self.authenticatedUser.email)
        self.assertEqual(self.attendee1.event, self.event)


    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi.delay')
    def test_edit_attendee_by_user(self, mocked_send_mail_multi):
        mutation = """
            mutation editEventAttendee($input: editEventAttendeeInput!) {
                editEventAttendee(input: $input) {
                    entity {
                        guid
                        attendees {
                            edges {
                                email
                                timeCheckedIn
                            }
                        }
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "emailAddress": self.authenticatedUser.email,
                "timeCheckedIn": None
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")
