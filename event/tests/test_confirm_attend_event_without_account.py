from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from django.test import override_settings
from django.utils.text import slugify
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ugettext_lazy
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

class ConfirmAttendEventWithoutAccountTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.event = mixer.blend(Event)
        self.event.max_attendees = 1
        self.event.attend_event_without_account = True
        self.event.save()
        EventAttendeeRequest.objects.create(code='1234567890', email='pete@test.test', event=self.event)

    def tearDown(self):
        self.event.delete()
        self.authenticatedUser.delete()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi')
    def test_confirm_attend_event_without_account(self, mocked_send_mail_multi):
        mutation = """
            mutation confirmAttendEventWithoutAccount($input: confirmAttendEventWithoutAccountInput!) {
                confirmAttendEventWithoutAccount(input: $input) {
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
                "code": "1234567890",
                "email": "pete@test.test"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        link = 'https://test.test/events/view/{}/{}'.format(self.event.guid, slugify(self.event.title)).lower()
        subject = ugettext_lazy("Confirmation of registration for %s" % self.event.title)

        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["guid"], self.event.guid)

        mocked_send_mail_multi.assert_called_once()

    @override_settings(ALLOWED_HOSTS=['test.test'])
    def test_confirm_attend_event_is_full_without_account(self):
        mutation = """
            mutation confirmAttendEventWithoutAccount($input: confirmAttendEventWithoutAccountInput!) {
                confirmAttendEventWithoutAccount(input: $input) {
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
                "code": "1234567890",
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
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "event_is_full")


    @override_settings(ALLOWED_HOSTS=['test.test'])
    def test_attend_event_without_account_attend_twice(self):
        mutation = """
            mutation confirmAttendEventWithoutAccount($input: confirmAttendEventWithoutAccountInput!) {
                confirmAttendEventWithoutAccount(input: $input) {
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
                "code": "1234567890",
                "email": "pete@test.test"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser
        request.META = {
            'HTTP_HOST': 'test.test'
        }
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_find")
