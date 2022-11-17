from unittest import mock

import faker
from django.utils import timezone
from mixer.backend.django import mixer

from core.lib import get_full_url
from core.tests.helpers import PleioTenantTestCase
from event.models import Event, EventAttendee
from user.factories import UserFactory


class TestWaitinglistMailerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.owner = UserFactory()

        self.event = mixer.blend(Event,
                                 owner=self.owner,
                                 location=faker.Faker().sentence(),
                                 location_address=faker.Faker().sentence(),
                                 location_link=faker.Faker().url(),
                                 start_date=timezone.localtime() + timezone.timedelta(days=9),
                                 max_attendees=10)

        self.attendee = mixer.blend(EventAttendee,
                                    event=self.event,
                                    user=self.user,
                                    email=self.user.email,
                                    state='waitinglist')

    @mock.patch('event.models.submit_mail_at_accept_from_waitinglist')
    def test_process_waitinglist_initiates_email(self, mocked_mail_initiative):
        self.event.process_waitinglist()

        assert mocked_mail_initiative.called, "Unexpectedly didn't call submit_mail_at_accept_from_waitinglist."

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_send_mail_function_schedules_mailer(self, mocked_manager_submit):
        from event.mail_builders.waitinglist import FromWaitinglistToAccept
        self.event.process_waitinglist()

        self.assertEqual(mocked_manager_submit.call_args.args, (FromWaitinglistToAccept,))
        self.assertEqual(mocked_manager_submit.call_args.kwargs, {
            'mailer_kwargs': {
                'event': self.event.guid,
                'attendee': self.attendee.id,
            }
        })

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mail_builder_parameters(self, mocked_build_context):
        from event.mail_builders.waitinglist import FromWaitinglistToAccept
        mocked_build_context.return_value = {}

        mailer = FromWaitinglistToAccept(event=self.event.guid,
                                         attendee=self.attendee.id)

        self.assertIn(self.event.title, mailer.get_subject())
        self.assertIsNone(mailer.get_sender())
        self.assertEqual(mailer.get_receiver(), self.attendee.user)
        self.assertEqual(mailer.get_receiver_email(), self.attendee.email)
        self.assertEqual(mailer.get_template(), 'email/attend_event_from_waitinglist.html')

        context = mailer.get_context()
        self.assertEqual(6, len(context.keys()))
        self.assertEqual(context['link'], get_full_url(self.event.url))
        self.assertEqual(context['location'], self.event.location)
        self.assertEqual(context['locationAddress'], self.event.location_address)
        self.assertEqual(context['locationLink'], self.event.location_link)
        self.assertEqual(context['start_date'], self.event.start_date)
        self.assertEqual(context['title'], self.event.title)
