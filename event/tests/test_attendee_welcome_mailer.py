from unittest import mock

from django.utils import timezone

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.mail_builders.attendee_welcome_mail import AttendeeWelcomeMailMailer
from event.models import EventAttendee
from user.factories import UserFactory


class TestAttendeeWelcomeMailerTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.attendee_user = UserFactory(name="ATTENDEE")

        self.event = EventFactory(owner=self.owner,
                                  attendee_welcome_mail_content=self.tiptap_paragraph("Hello [name] world!"),
                                  attendee_welcome_mail_subject="some subject")
        self.attendee = EventAttendee.objects.create(
            state='accept',
            user=self.attendee_user,
            event=self.event,
        )

        self.mailer = AttendeeWelcomeMailMailer(attendee=self.attendee.id)

    def tearDown(self):
        self.event.delete()
        self.attendee.delete()

        self.owner.delete()
        self.attendee_user.delete()

        super().tearDown()

    @mock.patch("event.mail_builders.attendee_welcome_mail.TemplateMailerBase.build_context")
    def test_attributes(self, build_context):
        build_context.return_value = {}

        self.assertDictEqual(self.mailer.get_context(), {"message": "<p>Hello ATTENDEE world!</p>",
                                                         "location": "",
                                                         "locationAddress": "",
                                                         "locationLink": "",
                                                         "start_date": self.event.start_date.astimezone(timezone.utc),
                                                         "subject": self.event.title, })
        self.assertEqual(self.mailer.get_language(), "nl")
        self.assertEqual(self.mailer.get_template(), "email/send_attendee_welcome_mail.html")
        self.assertEqual(self.mailer.get_receiver(), self.attendee_user)
        self.assertEqual(self.mailer.get_receiver_email(), self.attendee_user.email)
        self.assertEqual(self.mailer.get_subject(), self.event.attendee_welcome_mail_subject)
        self.assertEqual(self.mailer.get_sender(), None)
