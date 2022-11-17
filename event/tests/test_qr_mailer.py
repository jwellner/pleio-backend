import random
from email.mime.image import MIMEImage
from unittest import mock

import faker
from django.test import override_settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from event.mail_builders.qr_code import submit_mail_event_qr
from event.models import Event, EventAttendee
from user.factories import UserFactory
from user.models import User


class TestQrMailerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.group: Group = mixer.blend(Group)
        self.owner: User = UserFactory()
        self.event: Event = mixer.blend(Event,
                                        location=faker.Faker().sentence(),
                                        location_address=faker.Faker().address(),
                                        location_link=faker.Faker().url(),
                                        start_date=timezone.localtime() - timezone.timedelta(days=random.randint(-100, 100)),
                                        group=self.group,
                                        owner=self.owner,
                                        qr_access=True)
        self.event.read_access = [ACCESS_TYPE.group.format(self.group.id)]
        self.event.write_access = [ACCESS_TYPE.user.format(self.owner.id)]
        self.event.save()

        self.attendee = mixer.blend(EventAttendee,
                                    event=self.event,
                                    user=UserFactory())

        self.mutation = """
        mutation AttendToEvent(
                $input: attendEventInput!
            ) {
            attendEvent(
                    input: $input
                ) {
                entity {
                    guid
                }
            }
        }
        """
        self.variables = {
            "input": {
                "guid": self.event.guid,
                "state": "accept"
            }
        }

    @mock.patch('core.models.mail.MailInstanceManager.submit')
    def test_schedule_qr_code_mail(self, mailer_submit):
        from event.mail_builders.qr_code import QrMailer
        submit_mail_event_qr(self.attendee)

        assert mailer_submit.called, "MailInstance.objects.submit unexpectedly not called."
        self.assertEqual(mailer_submit.call_args.args, (QrMailer,))
        self.assertEqual(mailer_submit.call_args.kwargs, {'mailer_kwargs': {"attendee": self.attendee.id}})

    @mock.patch('event.resolvers.mutation_attend_event.submit_mail_event_qr')
    def test_attendee_got_mail_scheduled_for_him(self, mocked_send_event_qr):
        attending_user: User = mixer.blend(User)
        self.group.join(attending_user)

        self.graphql_client.force_login(attending_user)
        self.graphql_client.post(self.mutation, self.variables)

        assert mocked_send_event_qr.called, "submit_mail_event_qr unexpectedly not called."

        (attendee,) = mocked_send_event_qr.call_args.args
        self.assertEqual(attendee.email, attending_user.email)

    @mock.patch('event.models.submit_mail_event_qr')
    def test_attendee_from_waitinglist_to_accepted_got_mail_scheduled_for_him(self, mocked_send_event_qr):
        EventAttendee.objects.filter(id=self.attendee.id).update(state='waitinglist')

        self.event.process_waitinglist()

        assert mocked_send_event_qr.called, "submit_mail_event_qr unexpectedly not called."

    def test_mail_builder_parameters_not_yet_code(self):
        from event.mail_builders.qr_code import QrMailer
        EventAttendee.objects.filter(id=self.attendee.id).update(code=None)

        with mock.patch('event.mail_builders.qr_code.generate_code') as generate_code:
            generate_code.return_value = get_random_string(32)

            mailer = QrMailer(attendee=self.attendee.id)
            result = mailer.get_code()

            # created when not exists.
            self.attendee.refresh_from_db()
            self.assertTrue(generate_code.called)
            self.assertEqual(result, generate_code.return_value)
            self.assertEqual(self.attendee.code, generate_code.return_value)

    def test_mail_builder_parameters_with_code(self):
        from event.mail_builders.qr_code import QrMailer
        EventAttendee.objects.filter(id=self.attendee.id).update(code=get_random_string(32))
        self.attendee.refresh_from_db()

        with mock.patch('event.mail_builders.qr_code.generate_code') as generate_code:
            mailer = QrMailer(attendee=self.attendee.id)
            result = mailer.get_code()

            # not created when exists.
            self.assertFalse(generate_code.called)
            self.assertEqual(result, self.attendee.code)

    def test_mail_builder_parameters_filename(self):
        from event.mail_builders.qr_code import QrMailer
        event = mixer.blend(Event, title=faker.Faker().sentence())
        attendee = mixer.blend(EventAttendee, event=event)

        with mock.patch('event.mail_builders.qr_code.slugify') as mocked_slugify:
            mocked_slugify.return_value = get_random_string(length=10)
            mailer = QrMailer(attendee=attendee.id)
            result = mailer.get_filename()
            assert mocked_slugify.called, "slugify unexpectedly not called."
            assert mocked_slugify.return_value in result, "slug of event title not found in response"

    def test_mail_builder_parameters_filename_no_title(self):
        from event.mail_builders.qr_code import QrMailer
        event2 = mixer.blend(Event, title="")
        attendee2 = mixer.blend(EventAttendee, event=event2)

        with mock.patch('event.mail_builders.qr_code.slugify') as mocked_slugify:
            mocked_slugify.return_value = get_random_string(length=10)
            mailer = QrMailer(attendee=attendee2.id)
            result = mailer.get_filename()
            assert not mocked_slugify.called, "slugify unexpectedly called."
            assert mocked_slugify.return_value not in result, "slug of event title unexpectedly found in response"
            assert event2.guid in result, "slug of event title not found in response"

    def test_mail_builder_parameters_subject(self):
        from event.mail_builders.qr_code import QrMailer
        mailer = QrMailer(attendee=self.attendee.id)
        result = mailer.get_subject()
        assert self.event.title in result, "E-mail subject unexpectedly didn't contain event title."

    @override_settings(ENV='local')
    @mock.patch('event.mail_builders.qr_code.QrMailer.get_code')
    def test_mail_builder_parameters_qr_code_url(self, mocked_get_code):
        from event.mail_builders.qr_code import QrMailer
        mocked_get_code.return_value = "test_qr_code"
        mailer = QrMailer(attendee=self.attendee.id)
        result = mailer.get_qr_code_url()
        self.assertEqual(result, "http://tenant.fast-test.com:8000/events/view/guest-list?code=test_qr_code")

    def test_mail_builder_parameters_receiver_mail(self):
        from event.mail_builders.qr_code import QrMailer
        mailer = QrMailer(attendee=self.attendee.id)
        self.assertEqual(self.attendee.email, mailer.get_receiver_email())

    def test_mail_builder_parameters_receiver(self):
        from event.mail_builders.qr_code import QrMailer
        # Given.
        mailer = QrMailer(attendee=self.attendee.id)

        # When.
        result = mailer.get_receiver()

        # Then.
        self.assertIsNotNone(result)
        self.assertEqual(result, self.attendee.user)

        # Given.
        self.attendee.user = None
        self.attendee.save()
        mailer = QrMailer(attendee=self.attendee.id)

        # When.
        result = mailer.get_receiver()

        # Then.
        self.assertIsNone(result)

    def test_mail_builder_parameters_sender(self):
        from event.mail_builders.qr_code import QrMailer
        mailer = QrMailer(attendee=self.attendee.id)
        result = mailer.get_sender()

        self.assertIsNone(result)

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mail_builder_parameters_context(self, build_context):
        from event.mail_builders.qr_code import QrMailer
        build_context.return_value = {}

        # Given.
        mailer = QrMailer(attendee=self.attendee.id)

        # When.
        context = mailer.get_context()

        # Then.
        self.assertTrue(build_context.called)
        self.assertEqual(build_context.call_args.kwargs['user'], self.attendee.user)
        self.assertEqual(7, len(context))
        self.assertEqual(context['title'], self.event.title)
        self.assertEqual(context['location'], self.event.location)
        self.assertEqual(context['locationAddress'], self.event.location_address)
        self.assertEqual(context['locationLink'], self.event.location_link)
        self.assertEqual(context['startDate'], self.event.start_date)
        self.assertIn(self.event.url, context['link'])
        self.assertIn(mailer.content_id, context['qr_filename'])

    def test_mail_builder_parameters_template(self):
        from event.mail_builders.qr_code import QrMailer
        mailer = QrMailer(attendee=self.attendee.id)
        result = mailer.get_template()

        self.assertEqual(result, "email/attend_event_with_qr_access.html")

    def test_mail_builder_parameters_language(self):
        from event.mail_builders.qr_code import QrMailer
        mailer = QrMailer(attendee=self.attendee.id)
        result = mailer.get_language()

        self.assertEqual(result, self.attendee.language)

    @mock.patch('event.mail_builders.qr_code.QrMailer.get_qr_code_url')
    def test_mail_builder_parameters_attachment(self, get_qr_code_url):
        from event.mail_builders.qr_code import QrMailer
        get_qr_code_url.return_value = "for_testing"
        mailer = QrMailer(attendee=self.attendee.id)
        result = mailer.get_attachment()

        assert get_qr_code_url.called, "get_qr_code_url unexpectedly not called"
        assert isinstance(result, MIMEImage), f"Attachment unexpectedly isn't an instance of {MIMEImage}"

    @mock.patch('event.mail_builders.qr_code.QrMailer.get_attachment')
    def test_mail_builder_parameters_pre_send(self, mocked_get_attachment):
        from event.mail_builders.qr_code import QrMailer
        mocked_get_attachment.return_value = mock.MagicMock()
        mail_mock = mock.MagicMock()

        mailer = QrMailer(attendee=self.attendee.id)
        mailer.pre_send(mail_mock)

        self.assertTrue(mail_mock.attach.called, "pre_send didn't call email.attach.")
        self.assertEqual(mail_mock.attach.call_args.args, (mocked_get_attachment.return_value,))
