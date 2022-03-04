from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from backend2.schema import schema
from core.models import Group, GroupProfileFieldSetting, UserProfile
from event.models import Event, EventAttendee
from user.models import User


class EventsTestCase(FastTenantTestCase):

    def setUp(self):
        self.mutation = """"
                        mutation ($input: sendMessageToEventInput!) {
                            sendMessageToEvent(input: $input) {
                                success
                            }
                        }
                        """

        self.group = mixer.blend(Group)
        self.event = mixer.blend(Event, group=self.group)
        self.attendee = mixer.blend(User)
        self.group.join(self.attendee)
        self.event_attendee = mixer.blend(EventAttendee, event=self.event, user=self.attendee)
        self.owner = self.event.owner


    def test_setup_as_expected(self):
        self.assertIsNotNone(self.group)
        self.assertIsNotNone(self.event)
        self.assertIsNotNone(self.owner)
        self.assertIsNotNone(self.event_attendee)
        self.assertIsNotNone(self.attendee)

    def test_event_mail_attendees_view(self):
        request = HttpRequest()
        request.user = self.owner

        result = graphql_sync(schema, { "query": self.mutation , "variables": {}}, context_value={ "request": request })

        self.assertEqual([], result, msg=result)


