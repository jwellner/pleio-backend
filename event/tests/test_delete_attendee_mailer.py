from unittest import mock

from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from event.mail_builders.delete_event_attendees import DeleteEventAttendeeMailer
from event.models import EventAttendee
from user.factories import UserFactory


class TestDeleteAttendeeMailerTestCase(PleioTenantTestCase):

    def setUp(self):
        super(TestDeleteAttendeeMailerTestCase, self).setUp()

        self.participant = UserFactory(name="Participant")
        self.event = EventFactory(UserFactory(), title="Test event")
        self.attendee = mixer.blend(EventAttendee,
                                    event=self.event,
                                    user=self.participant)
        self.mailer = DeleteEventAttendeeMailer(mail_info=self.participant.as_mailinfo(),
                                                event=self.event.guid,
                                                user=self.participant.guid)

    def test_called_from_the_right_spot(self):
        """
        @see tests.event.test_delete_event_attendees.DeleteEventAttendeesTestCase.test_delete_attendees_from_event_by_user
        @see tests.event.test_delete_event_attendees.DeleteEventAttendeesTestCase.test_delete_attendees_from_event_by_owner
        """
        pass

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mailer_attribute_context(self, mocked_build_context):
        mocked_build_context.return_value = {}

        context = self.mailer.get_context()
        self.assertEqual(3, len(context))
        self.assertIn(self.event.url, context['link'])
        self.assertEqual(self.event.title, context['title'])
        self.assertEqual(self.participant.name, context['removed_attendee_name'])

    def test_mailer_attributes(self):
        self.assertEqual(self.participant.get_language(), self.mailer.get_language())
        self.assertEqual("email/delete_event_attendees.html", self.mailer.get_template())
        self.assertEqual(self.participant, self.mailer.get_receiver())
        self.assertEqual(self.participant.email, self.mailer.get_receiver_email())
        self.assertIsNone(self.mailer.get_sender())
        self.assertIn(self.event.title, self.mailer.get_subject())
