from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from user.models import User
from event.models import Event, EventAttendee
from mixer.backend.django import mixer
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

    @mock.patch('event.resolvers.mutation_attend_event.generate_code', return_value='6df8cdad5582833eeab4')
    def test_create_attend_event_without_account_request(self, mocked_generate_code):
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
                "email": "pete@tenant.fast-test.com"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        link = "https://tenant.fast-test.com/events/confirm/" + self.event.guid + "?email=pete@tenant.fast-test.com&code=6df8cdad5582833eeab4"
        subject = "Confirmation of registration %s" % self.event.title
        context = {'link': link, 'title': self.event.title, 'location': self.event.location, 'start_date': self.event.start_date}
        self.assertEqual(data["attendEventWithoutAccount"]["entity"]["guid"], self.event.guid)
        self.assertEqual(data["attendEventWithoutAccount"]["entity"]["title"], self.event.title)


    @mock.patch('event.resolvers.mutation_attend_event.generate_code', return_value='6df8cdad5582833eeab4')
    def test_attend_event_without_account_resend(self, mocked_generate_code):
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
                "email": "pete@tenant.fast-test.com"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        variables = {
            "input": {
                "guid": self.event.guid,
                "name": "pete",
                "email": "pete@tenant.fast-test.com",
                "resend": True
            }
        }
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        link = "https://tenant.fast-test.com/events/confirm/" + self.event.guid + "?email=pete@tenant.fast-test.com&code=6df8cdad5582833eeab4"
        subject = "Confirmation of registration %s" % self.event.title

        self.assertEqual(data["attendEventWithoutAccount"]["entity"]["guid"], self.event.guid)
        self.assertEqual(data["attendEventWithoutAccount"]["entity"]["title"], self.event.title)

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
                "email": "pete@tenant.fast-test.com"
            }
        }

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "email_already_used")

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
                "email": "pete@tenant.fast-test.com"
            }
        }
        EventAttendee.objects.create(
            event=self.event,
            state='accept',
            user=self.authenticatedUser,
            email=self.authenticatedUser.email
        )

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        
        self.assertTrue(result[0])


    @mock.patch('event.resolvers.mutation_attend_event.generate_code', return_value='6df8cdad5582833eeab4')
    def test_attend_event_without_account_no_name(self, mocked_generate_code):
        variables = {
            "input": {
                "guid": self.event.guid,
                "name": "",
                "email": "pete@tenant.fast-test.com"
            }
        }
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

        request = HttpRequest()
        request.user = self.anonymousUser

        result = graphql_sync(schema, { "query": mutation, "variables": variables }, context_value={ "request": request })
        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "invalid_name")