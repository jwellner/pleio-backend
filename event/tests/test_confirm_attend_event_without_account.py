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

class ConfirmAttendEventWithoutAccountTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.event = mixer.blend(Event)
        self.event.max_attendees = 1
        self.event.attend_event_without_account = True
        self.event.save()
        EventAttendeeRequest.objects.create(code='1234567890', email='pete@tenant.fast-test.com', event=self.event)
        EventAttendeeRequest.objects.create(code='1234567890', email='test@tenant.fast-test.com', event=self.event)

    def tearDown(self):
        self.event.delete()
        self.authenticatedUser.delete()

    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi.delay')
    def test_confirm_attend_event_without_account(self, mocked_send_mail_multi):
        mutation = """
            mutation confirmAttendEventWithoutAccount($input: confirmAttendEventWithoutAccountInput!) {
                confirmAttendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        attendees {
                            total
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
                "guid": self.event.guid,
                "code": "1234567890",
                "email": "pete@tenant.fast-test.com"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["guid"], self.event.guid)
        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["attendees"]["edges"], [])

        mocked_send_mail_multi.assert_called_once()

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
                "email": "pete@tenant.fast-test.com"
            }
        }

        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=self.authenticatedUser
        )

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "event_is_full")

    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi.delay')
    def test_confirm_delete_attend_event_without_account(self, mocked_send_mail_multi):
        mutation = """
            mutation confirmAttendEventWithoutAccount($input: confirmAttendEventWithoutAccountInput!) {
                confirmAttendEventWithoutAccount(input: $input) {
                    entity {
                        guid
                        attendees {
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
                "guid": self.event.guid,
                "code": "1234567890",
                "email": "test@tenant.fast-test.com",
                "delete": True
            }
        }

        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=None,
            email='test@tenant.fast-test.com'
        )

        request = HttpRequest()
        request.user = self.anonymousUser

        self.assertEqual(self.event.attendees.exclude(user__isnull=False).count(), 1)

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        data = result[1]["data"]

        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["guid"], self.event.guid)
        self.assertEqual(data["confirmAttendEventWithoutAccount"]["entity"]["attendees"]["edges"], [])
        self.assertEqual(self.event.attendees.exclude(user__isnull=False).count(), 0)


    def test_confirm_attend_event_is_full_without_account_waitinglist(self):
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
                "state": "waitinglist",
                "email": "pete@tenant.fast-test.com"

            }
        }

        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=self.authenticatedUser
        )

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        
        self.assertEqual(self.event.attendees.filter(state='waitinglist').count(), 1)


    @mock.patch('event.resolvers.mutation_confirm_attend_event_without_account.send_mail_multi.delay')
    def test_confirm_attend_event_without_account_subevent_without_parent(self, mocked_send_mail_multi):
        
        subevent = mixer.blend(Event)
        subevent.parent = self.event
        subevent.attend_event_without_account = True
        subevent.save()
        EventAttendeeRequest.objects.create(code='1234567890', email='pete@tenant.fast-test.com', event=subevent)
        
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
                "guid": subevent.guid,
                "code": "1234567890",
                "email": "pete@tenant.fast-test.com",
                "state": "accept"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "not_attending_parent_event")
