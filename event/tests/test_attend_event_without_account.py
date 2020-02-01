from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ugettext_lazy
from django.http import HttpRequest
from core.models import Group, User
from event.models import Event, EventAttendee
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer
from graphql import GraphQLError
from datetime import datetime
from unittest import mock

class AttendEventWithoutAccountTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.event = mixer.blend(Event)
        self.event.max_attendees = 1
        self.event.save()
    def tearDown(self):
        self.event.delete()
        self.authenticatedUser.delete()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('event.resolvers.mutation_attend_event_without_account.generate_code', return_value='6df8cdad5582833eeab4')
    @mock.patch('event.resolvers.mutation_attend_event_without_account.send_mail_multi')
    def test_attend_event_without_account(self, mocked_send_mail_multi, mocked_generate_code):
        mutation = """
            mutation RequestAttendance($input: attendEventWithoutAccountInput!) {
                attendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        ... on Event {
                            title
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "name": "pete",
                "email": "pete@test.test"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        link = "https://test.test/events/confirm/" + self.event.guid + "?email=pete@test.test&code=6df8cdad5582833eeab4"
        subject = ugettext_lazy("Confirmation of registration %s" % self.event.title)
        context = {'link': link, 'title': self.event.title, 'location': self.event.location, 'start_date': self.event.start_date}
        self.assertEqual(data["attendEventWithoutAccount"]["entity"]["guid"], self.event.guid)
        self.assertEqual(data["attendEventWithoutAccount"]["entity"]["title"], self.event.title)

        mocked_send_mail_multi.assert_called_once()


    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('event.resolvers.mutation_attend_event_without_account.generate_code', return_value='6df8cdad5582833eeab4')
    @mock.patch('event.resolvers.mutation_attend_event_without_account.send_mail_multi')
    def test_attend_event_without_account_resend(self, mocked_send_mail_multi, mocked_generate_code):
        mutation = """
            mutation RequestAttendance($input: attendEventWithoutAccountInput!) {
                attendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        ... on Event {
                            title
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "name": "pete",
                "email": "pete@test.test"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)
        mocked_send_mail_multi.assert_called_once()
        variables = {
            "input": {
                "guid": self.event.guid,
                "name": "pete",
                "email": "pete@test.test",
                "resend": True
            }
        }
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        data = result[1]["data"]

        link = "https://test.test/events/confirm/" + self.event.guid + "?email=pete@test.test&code=6df8cdad5582833eeab4"
        subject = ugettext_lazy("Confirmation of registration %s" % self.event.title)

        self.assertEqual(data["attendEventWithoutAccount"]["entity"]["guid"], self.event.guid)
        self.assertEqual(data["attendEventWithoutAccount"]["entity"]["title"], self.event.title)

    @override_settings(ALLOWED_HOSTS=['test.test'])
    def test_attend_event_without_account_attend_twice(self):
        mutation = """
            mutation RequestAttendance($input: attendEventWithoutAccountInput!) {
                attendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        ... on Event {
                            title
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "name": "pete",
                "email": "pete@test.test"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "email_already_used")

    @override_settings(ALLOWED_HOSTS=['test.test'])
    def test_attend_event_is_full_without_account(self):
        mutation = """
            mutation RequestAttendance($input: attendEventWithoutAccountInput!) {
                attendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        ... on Event {
                            title
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """

        variables = {
            "input": {
                "guid": self.event.guid,
                "name": "pete",
                "email": "pete@test.test"
            }
        }
        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=self.authenticatedUser
        )

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value=request)
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "event_is_full")
