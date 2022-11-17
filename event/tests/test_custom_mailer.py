from unittest import mock

from django.utils.translation import gettext as _
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.lib import get_full_url
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from event.models import Event, EventAttendee
from user.models import User


class TestCustomMailerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.mutation = """
            mutation ($input: sendMessageToEventInput!) {
                sendMessageToEvent(input: $input) {
                    success,
                    messageCount
                }
            }
            """

        self.group = mixer.blend(Group)
        self.owner = mixer.blend(User, email="owner@example.net")
        self.event = mixer.blend(Event, group=self.group, owner=self.owner)
        self.event.write_access = [ACCESS_TYPE.user.format(self.owner.id)]
        self.event.save()

        self.attending_user = mixer.blend(User, email="attending-user@example.net")
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

        self.fourth_attendee = mixer.blend(EventAttendee,
                                           event=self.event, name="Hippo", email="hippo@example.com", state='accept')

        self.outsider = mixer.blend(User)

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_event_mail_attendees_access(self, mailer_submit):
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
        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, variables)
        self.assertEqual(2, result['data']['sendMessageToEvent']['messageCount'])
        self.assertEqual(2, mailer_submit.call_count)

        # Test attendee.
        with self.assertGraphQlError('not_authorized'):
            self.graphql_client.force_login(self.attending_user)
            self.graphql_client.post(self.mutation, variables)

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_event_mailer_should_send_test_mail_to_sender(self, mailer_submit):
        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': True,
            }
        }

        self.graphql_client.force_login(self.owner)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(1, mailer_submit.call_count)

        kwargs = mailer_submit.call_args.kwargs['mailer_kwargs']

        self.assertEqual(kwargs['event'], self.event.guid)
        self.assertEqual(kwargs['sender'], self.owner.guid)
        self.assertEqual(kwargs['message'], 'expected message')
        self.assertEqual(kwargs['subject'], 'expected subject')
        self.assertEqual(kwargs['copy'], False)
        self.assertEqual(kwargs['mail_info'], self.owner.as_mailinfo())

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_event_mailer_should_send_test_mail_to_sender_only(self, mailer_submit):
        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': True,
                'sendToAttendees': True,
            }
        }

        self.graphql_client.force_login(self.owner)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(1, mailer_submit.call_count)

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_event_mailer_should_send_mail_to_attendees(self, mailer_submit):
        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': False,
                'sendToAttendees': True,
            }
        }

        self.graphql_client.force_login(self.owner)
        self.graphql_client.post(self.mutation, variables)

        self.assertEqual(4, mailer_submit.call_count)

        mail_infos = [c.kwargs['mailer_kwargs']['mail_info'] for c in mailer_submit.call_args_list]

        self.assertIn(self.event_attendee.as_mailinfo(), mail_infos)
        self.assertIn(self.second_attendee.as_mailinfo(), mail_infos)
        self.assertIn(self.third_attendee.as_mailinfo(), mail_infos)
        self.assertIn(self.fourth_attendee.as_mailinfo(), mail_infos)

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_event_mailer_should_send_copy_to_sender(self, mailer_submit):
        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': False,
                'sendCopyToSender': True,
            }
        }

        self.graphql_client.force_login(self.owner)
        self.graphql_client.post(self.mutation, variables)
        kwargs = mailer_submit.call_args.kwargs['mailer_kwargs']

        self.assertEqual(kwargs['mail_info'], self.owner.as_mailinfo())

        class FoundIt(Exception):
            pass

        with self.assertRaises(FoundIt):
            for c in mailer_submit.call_args_list:
                kwargs = c.kwargs['mailer_kwargs']
                if kwargs['mail_info'] == self.owner.as_mailinfo() and kwargs['copy'] == True:
                    raise FoundIt()

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_event_mailer_should_send_one_test_message(self, mailer_submit):
        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': True,
                'sendToAttendees': True,
            }
        }

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, variables)

        self.assertEqual(result['data']['sendMessageToEvent']['messageCount'], 1)

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_event_mailer_should_give_feedback_about_multiple_attendees(self, mailer_submit):
        variables = {
            'input': {
                'guid': self.event.guid,
                'subject': "expected subject",
                'message': "expected message",
                'isTest': False,
                'sendToAttendees': True,
            }
        }

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, variables)

        self.assertEqual(result['data']['sendMessageToEvent']['messageCount'], 4)

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_event_mailer_should_give_feedback_about_multiple_attendees_and_a_copy(self, mailer_submit):
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

        self.graphql_client.force_login(self.owner)
        result = self.graphql_client.post(self.mutation, variables)

        self.assertEqual(result['data']['sendMessageToEvent']['messageCount'], 5)

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mail_builder_parameters(self, mocked_build_context):
        from event.mail_builders.custom_message import CustomMessageMailer
        mocked_build_context.return_value = {}

        expected_subject = "expected_subject"
        expected_message = "Hello world!"

        mailer = CustomMessageMailer(
            event=self.event.guid,
            sender=self.owner.guid,
            message=expected_message,
            subject=expected_subject,
            mail_info=self.attending_user.as_mailinfo(),
        )
        context = mailer.get_context()

        self.assertIn(expected_subject, mailer.get_subject())
        self.assertEqual(mailer.get_sender(), self.owner)
        self.assertEqual(mailer.get_receiver(), self.attending_user)
        self.assertEqual(mailer.get_receiver_email(), self.attending_user.email)
        self.assertEqual(mailer.get_language(), self.attending_user.get_language())
        self.assertEqual(mailer.get_template(), 'email/send_message_to_event.html')

        self.assertEqual(mocked_build_context.call_args.kwargs, {
            'user': self.owner,
        })
        self.assertEqual(3, len(context.keys()))
        self.assertEqual(context['event'], self.event.title)
        self.assertEqual(context['event_url'], get_full_url(self.event.url))
        self.assertEqual(context['message'], expected_message)

    def test_event_mailer_should_give_copy_in_the_subject_of_copies(self):
        from event.mail_builders.custom_message import CustomMessageMailer

        expected_subject = "expected_subject"
        mailer = CustomMessageMailer(
            event=self.event.guid,
            sender=self.owner.guid,
            message="Hello world!",
            subject=expected_subject,
            mail_info=self.attending_user.as_mailinfo(),
            copy=True,
        )

        self.assertEqual(mailer.get_subject(),
                         _("Copy: Message from event {0}: {1}").format(self.event.title, expected_subject))
