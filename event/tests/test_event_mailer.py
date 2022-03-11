from unittest import mock

from ariadne import graphql_sync
from django.http import HttpRequest
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from backend2.schema import schema
from core.constances import ACCESS_TYPE
from core.models import Group
from core.utils.test import suppress_stdout
from event.models import Event, EventAttendee
from user.models import User


class EventsTestCase(FastTenantTestCase):

    def setUp(self):
        self.mutation = """
            mutation ($input: sendMessageToEventInput!) {
                sendMessageToEvent(input: $input) {
                    success,
                    messageCount
                }
            }
            """

        self.group = mixer.blend(Group)
        self.owner = mixer.blend(User)
        self.event = mixer.blend(Event, group=self.group, owner=self.owner)
        self.event.write_access = [ACCESS_TYPE.user.format(self.owner.id)]
        self.event.save()

        self.attending_user = mixer.blend(User)
        self.event_attendee = mixer.blend(EventAttendee,
                                          event=self.event, user=self.attending_user, state='accept')

        self.waiting_user = mixer.blend(User)
        self.event_waiting_attendee = mixer.blend(EventAttendee,
                                                  event=self.event, user=self.waiting_user, state='waitinglist')

        self.maybe_attending_user = mixer.blend(User)
        self.event_maybe_attendee = mixer.blend(EventAttendee,
                                                event=self.event, user=self.maybe_attending_user, state='maybe')

        self.rejected_user = mixer.blend(User)
        self.event_rejected_attendee = mixer.blend(EventAttendee,
                                                   event=self.event, user=self.rejected_user, state='reject')

        self.second_attendee = mixer.blend(EventAttendee,
                                           event=self.event, user=mixer.blend(User), state='accept')
        self.third_attendee = mixer.blend(EventAttendee,
                                          event=self.event, user=mixer.blend(User), state='accept')

        self.outsider = mixer.blend(User)

    def test_event_mail_attendees_access(self):
        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': True,
                'sendToAttendees': True,
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
            request.user = self.attending_user
            success, result = graphql_sync(schema, {"query": self.mutation,
                                                    "variables": variables},
                                           context_value={"request": request})

        self.assertIn('errors', result,
                      msg="graphql geeft aan dat er geen fouten zijn, maar een attendee mag helemaal geen mail sturen.")

    @mock.patch('event.resolvers.mutation_messages.SendEventMessage.populate')
    @mock.patch('event.resolvers.mutation_messages.SendEventMessage.send')
    def test_event_mailer_should_send_test_mail_to_sender(self, mocked_sender_send, mocked_sender_prepare):
        request = HttpRequest()
        request.user = self.owner

        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': True,
            }
        }

        success, result = graphql_sync(schema, {"query": self.mutation,
                                                "variables": variables},
                                       debug=False,
                                       context_value={"request": request})
        self.assertTrue('errors' not in result, msg=result)
        mocked_sender_prepare.assert_called_with(event=self.event,
                                                 sender=self.owner,
                                                 message=variables['input']['message'],
                                                 subject=variables['input']['subject'])
        mocked_sender_send.assert_called_with(receiving_user=self.owner,
                                              copy=False)

    @mock.patch('event.resolvers.mutation_messages.SendEventMessage.send')
    def test_event_mailer_should_send_test_mail_to_sender_only(self, mocked_sender_send):
        request = HttpRequest()
        request.user = self.owner

        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': True,
                'sendToAttendees': True,
            }
        }

        success, result = graphql_sync(schema, {"query": self.mutation,
                                                "variables": variables},
                                       debug=False,
                                       context_value={"request": request})
        self.assertTrue('errors' not in result, msg=result)

        mocked_sender_send.assert_called_once_with(receiving_user=self.owner,
                                                   copy=False)

    @mock.patch('event.resolvers.mutation_messages.SendEventMessage.send')
    def test_event_mailer_should_send_mail_to_attendees(self, mocked_sender_send):
        request = HttpRequest()
        request.user = self.owner

        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': False,
                'sendToAttendees': True,
            }
        }

        success, result = graphql_sync(schema, {"query": self.mutation,
                                                "variables": variables},
                                       debug=False,
                                       context_value={"request": request})
        self.assertTrue('errors' not in result, msg=result)

        mocked_sender_send.assert_any_call(receiving_user=self.attending_user,
                                           copy=False)
        mocked_sender_send.assert_any_call(receiving_user=self.second_attendee.user,
                                           copy=False)
        mocked_sender_send.assert_any_call(receiving_user=self.third_attendee.user,
                                           copy=False)

    @mock.patch('event.resolvers.mutation_messages.SendEventMessage.send')
    def test_event_mailer_should_send_copy_to_sender(self, mocked_sender_send):
        request = HttpRequest()
        request.user = self.owner

        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': False,
                'sendCopyToSender': True,
            }
        }

        success, result = graphql_sync(schema, {"query": self.mutation,
                                                "variables": variables},
                                       debug=False,
                                       context_value={"request": request})
        self.assertTrue('errors' not in result, msg=result)

        mocked_sender_send.assert_called_once_with(receiving_user=self.owner,
                                                   copy=True)

    def test_event_mailer_should_send_one_test_message(self):
        request = HttpRequest()
        request.user = self.owner

        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': True,
                'sendToAttendees': True,
            }
        }

        success, result = graphql_sync(schema, {"query": self.mutation,
                                                "variables": variables},
                                       debug=False,
                                       context_value={"request": request})

        self.assertTrue('errors' not in result, msg=result)
        self.assertEqual(result['data']['sendMessageToEvent']['messageCount'], 1)

    def test_event_mailer_should_give_feedback_about_multiple_attendees(self):
        request = HttpRequest()
        request.user = self.owner

        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': False,
                'sendToAttendees': True,
            }
        }

        success, result = graphql_sync(schema, {"query": self.mutation,
                                                "variables": variables},
                                       debug=False,
                                       context_value={"request": request})

        self.assertTrue('errors' not in result, msg=result)
        self.assertEqual(result['data']['sendMessageToEvent']['messageCount'], 3)

    def test_event_mailer_should_give_feedback_about_multiple_attendees_and_a_copy(self):
        request = HttpRequest()
        request.user = self.owner

        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': False,
                'sendToAttendees': True,
                'sendCopyToSender': True,
            }
        }

        success, result = graphql_sync(schema, {"query": self.mutation,
                                                "variables": variables},
                                       debug=False,
                                       context_value={"request": request})

        self.assertTrue('errors' not in result, msg=result)
        self.assertEqual(result['data']['sendMessageToEvent']['messageCount'], 4)

    @mock.patch('event.resolvers.mutation_messages.send_mail_multi.delay')
    def test_event_mailer_should_give_event_name_and_subject_in_mail_subject(self, mocked_send_mail_multi):
        from event.resolvers.mutation_messages import SendEventMessage

        expected_subject = "expected_subject"

        mailer = SendEventMessage()
        mailer.populate(self.event, self.owner, "", expected_subject)

        mailer.send(self.owner, copy=False)

        self.assertEqual(mocked_send_mail_multi.call_args.kwargs['subject'], "Message from event {event}: {subject}".format(
            event=self.event.title,
            subject=expected_subject
        ))

    @mock.patch('event.resolvers.mutation_messages.send_mail_multi.delay')
    def test_event_mailer_should_give_copy_in_the_subject_of_copies(self, mocked_send_mail_multi):
        from event.resolvers.mutation_messages import SendEventMessage

        expected_subject = "expected_subject"

        mailer = SendEventMessage()
        mailer.populate(self.event, self.owner, "", expected_subject)

        mailer.send(self.owner, copy=True)

        self.assertEqual(mocked_send_mail_multi.call_args.kwargs['subject'], "Copy: Message from event {event}: {subject}".format(
            event=self.event.title,
            subject=expected_subject
        ))
