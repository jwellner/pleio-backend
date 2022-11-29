from unittest import mock
from unittest.mock import MagicMock

from django.utils.crypto import get_random_string
from faker import Faker
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.mail_builders.attend_event_confirm import AttendEventWithoutAccountConfirmMailer
from event.models import EventAttendee
from tenants.helpers import FastTenantTestCase
from user.factories import UserFactory


class TestAttendEventWithoutAccountConfirmMailerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.event = EventFactory(owner=UserFactory(),
                                  title="Test event",
                                  location=Faker().sentence(),
                                  location_link=Faker().url(),
                                  location_address=Faker().address())
        self.code = get_random_string(10)
        self.attendee = mixer.blend(EventAttendee,
                                    state='accept',
                                    email=Faker().email(),
                                    name=Faker().name(),
                                    event=self.event)
        self.mailer = AttendEventWithoutAccountConfirmMailer(attendee=self.attendee.id,
                                                             code=self.code)

    def test_called_from_the_right_spot(self):
        """
        @see tests.event.test_confirm_attend_event_without_account.ConfirmAttendEventWithoutAccountTestCase.test_confirm_attend_event_without_account
        """
        pass

    @mock.patch('event.mail_builders.attend_event_confirm.LeaveUrl.__init__')
    @mock.patch('event.mail_builders.attend_event_confirm.LeaveUrl.add_email')
    @mock.patch('event.mail_builders.attend_event_confirm.LeaveUrl.add_code')
    @mock.patch('event.mail_builders.attend_event_confirm.LeaveUrl.get_url')
    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mailer_attribute_context(self, mocked_build_context, get_url, add_code, add_email, url_init):
        mocked_build_context.return_value = {}
        url_init.return_value = None
        get_url.return_value = Faker().url()

        context = self.mailer.get_context()

        assert get_url.called
        self.assertEqual(self.code, add_code.call_args.args[0])
        self.assertEqual(self.attendee.email, add_email.call_args.args[0])
        self.assertEqual(self.event, url_init.call_args.args[0])

        self.assertEqual(8, len(context))
        self.assertIn(self.event.url, context['link'])
        self.assertIn(get_url.return_value, context['leave_link'])
        self.assertEqual(self.event.title, context['title'])
        self.assertEqual(self.event.location, context['location'])
        self.assertEqual(self.event.location_link, context['locationLink'])
        self.assertEqual(self.event.location_address, context['locationAddress'])
        self.assertEqual(self.event.start_date, context['start_date'])
        self.assertEqual(self.attendee.state, context['state'])

    def test_mailer_attributes(self):
        self.assertEqual("email/attend_event_without_account_confirm.html", self.mailer.get_template())
        self.assertEqual(self.attendee.language, self.mailer.get_language())
        self.assertEqual(self.attendee.email, self.mailer.get_receiver_email())
        self.assertIsNone(self.mailer.get_receiver())
        self.assertIsNone(self.mailer.get_sender())
        self.assertIn(self.event.title, self.mailer.get_subject())


class TestLeaveUrlTestCase(FastTenantTestCase):
    def setUp(self):
        super().setUp()
        from event.mail_builders.attend_event_confirm import LeaveUrl
        self.event = MagicMock()
        self.event.guid = "demo"
        self.leave_url = LeaveUrl(self.event)

    def test_url(self):
        self.assertEqual('/events/confirm/demo?delete=true', self.leave_url.get_url())

    def test_url_with_mail(self):
        email = Faker().email()
        self.leave_url.add_email(email)
        self.assertEqual(f'/events/confirm/demo?delete=true&email={email}', self.leave_url.get_url())

    def test_url_with_code(self):
        code = get_random_string(10)
        self.leave_url.add_code(code)
        self.assertEqual(f'/events/confirm/demo?delete=true&code={code}', self.leave_url.get_url())
