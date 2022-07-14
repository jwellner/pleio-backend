from unittest import mock

import faker
from django.utils import timezone
from mixer.backend.django import mixer

from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestAttendEventMailerTestCase(PleioTenantTestCase):

    def setUp(self):
        super(TestAttendEventMailerTestCase, self).setUp()

        from event.models import Event
        self.event = mixer.blend(Event,
                                 location=faker.Faker().sentence(),
                                 location_address=faker.Faker().sentence(),
                                 location_link=faker.Faker().url(),
                                 start_date=timezone.localtime()-timezone.timedelta(days=100, hours=10),
                                 attend_event_without_account=True)
        self.user = UserFactory()

    @mock.patch('event.resolvers.mutation_attend_event.submit_attend_event_wa_request')
    def test_send_mail_called_when_attend_to_event_without_email(self, mocked_attend_event_mail):
        from event.models import EventAttendeeRequest
        query = """
        mutation AttendEventWithoutAccount($input: attendEventWithoutAccountInput!) {
            attendEventWithoutAccount(input: $input) {
                entity {
                    guid
                }
            }
        }
        """

        self.graphql_client.post(query, {
            'input': {
                'guid': str(self.event.id),
                'name': self.user.name,
                'email': self.user.email,
            }
        })

        attendee_request = EventAttendeeRequest.objects.get(event=self.event, email=self.user.email)

        assert mocked_attend_event_mail.called, "Unexpectedly did not call submit_attend_event_wa_request"
        (kwargs,) = mocked_attend_event_mail.call_args.args
        self.assertEqual(4, len(kwargs), msg="Unexpectedly called with another set of keyword arguments")
        self.assertEqual(kwargs['event'], self.event.guid)
        self.assertEqual(kwargs['email'], self.user.email)
        self.assertIn('language', kwargs)
        self.assertIn(f"/events/confirm/{self.event.guid}", kwargs['link'])
        self.assertIn(f"?email={self.user.email}", kwargs['link'])
        self.assertIn(f"&code={attendee_request.code}", kwargs['link'])

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mail_builder_parameters(self, mocked_build_context):
        from event.mail_builders.attend_event_request import AttendWithoutAccountMailer
        mocked_build_context.return_value = {}
        LINK = faker.Faker().url()

        mailer = AttendWithoutAccountMailer(
            event=self.event.guid,
            email=self.user.email,
            language=self.user.get_language(),
            link=LINK
        )

        self.assertIn(self.event.title, mailer.get_subject())
        self.assertEqual(mailer.get_receiver_email(), self.user.email)
        self.assertEqual(mailer.get_language(), self.user.get_language())
        self.assertEqual(mailer.get_template(), 'email/attend_event_without_account.html')
        self.assertEqual(mailer.get_sender(), None)
        self.assertEqual(mailer.get_receiver(), None)

        context = mailer.get_context()
        self.assertEqual(6, len(context))
        self.assertEqual(context["link"], LINK)
        self.assertEqual(context["location"], self.event.location)
        self.assertEqual(context["locationAddress"], self.event.location_address)
        self.assertEqual(context["locationLink"], self.event.location_link)
        self.assertDateEqual(str(context["start_date"]), str(self.event.start_date))
        self.assertEqual(context["title"], self.event.title)
