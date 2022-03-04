from contextlib import contextmanager

from ariadne import graphql_sync
from django.http import HttpRequest
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from backend2.schema import schema
from core.constances import ACCESS_TYPE
from core.models import Group
from event.models import Event, EventAttendee
from user.models import User


class EventsTestCase(FastTenantTestCase):

    def setUp(self):
        self.mutation = """
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

        self.owner = mixer.blend(User)
        self.group.join(self.owner)

        self.event.write_access = [ACCESS_TYPE.user.format(self.owner.id)]
        self.event.save()

        self.event_attendee = mixer.blend(EventAttendee, event=self.event, user=self.attendee)

    def test_event_mail_attendees_access(self):
        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'sendTest': True,
                'sendToAttendees': True,
                'sendToWaitinglist': True,
                'sendCopyToSender': True,
            }
        }

        # Test owner.
        request = HttpRequest()
        request.user = self.owner
        success, result = graphql_sync(schema, {"query": self.mutation,
                                                "variables": variables},
                                       debug=False,
                                       context_value={"request": request})
        self.assertTrue('errors' not in result, msg=result)

        # Test attendee.
        with suppress_stdout():
            request = HttpRequest()
            request.user = self.attendee
            success, result = graphql_sync(schema, {"query": self.mutation,
                                                    "variables": variables},
                                           context_value={"request": request})

        self.assertIn('errors', result,
                      msg="graphql geeft aan dat er geen fouten zijn, maar een attendee mag helemaal geen mail sturen.")


@contextmanager
def suppress_stdout():
    from contextlib import redirect_stderr, redirect_stdout
    from os import devnull

    with open(devnull, 'w') as fnull:
        with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
            yield (err, out)
