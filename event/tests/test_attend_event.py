from unittest import mock

from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from backend2.schema import schema
from core.constances import ACCESS_TYPE
from event.models import Event, EventAttendeeRequest
from user.models import User


class AttendEventTestCase(FastTenantTestCase):
    #TODO: test mail

    def setUp(self):
        self.authenticatedUser = mixer.blend(User)
        self.event = mixer.blend(
            Event, 
            qr_access=True,
            read_access=[ACCESS_TYPE.public], 
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            attend_event_without_account=True
        )
        self.anonymousUser = AnonymousUser()
        EventAttendeeRequest.objects.create(code='1234567890', email='pete@tenant.fast-test.com', event=self.event)

    
    def tearDown(self):
        self.event.delete()
        self.authenticatedUser.delete()

    def test_attend_event_with_qr_access(self):
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
                "guid": self.event.guid,
                "state": 'accept'
            }
        }

        request = HttpRequest()
        request.user = self.authenticatedUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        
        self.assertTrue(result[0])
    
    def test_attend_event_with_qr_access_without_account(self):
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

        self.assertTrue(result[0])
