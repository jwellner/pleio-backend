from unittest import mock

from core.factories import GroupFactory
from core.mail_builders.group_welcome import GroupWelcomeMailer
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, EditorFactory
from user.models import User


class TestGroupWelcomeMailerTestCase(PleioTenantTestCase):

    BLANK_HTML =  "<h2></h2><p>\n\n</p>  <p><strong>  \t\t</strong>"

    def setUp(self):
        super().setUp()

        self.owner: User = EditorFactory()
        self.member: User = UserFactory()
        self.user: User = UserFactory()
        self.group: Group = GroupFactory(name="Messaged group",
                                         owner=self.owner,
                                         welcome_message="""
            Welkom vrolijke vriend [name],<br>
            <br>
            Hier bij <a href="[group_url]">[group_name]</a> zijn we heel blij met nieuwe leden.<br>
            <br>
            Nou... dag hoor!<br>
        """)
        self.group.join(self.member)

        self.mailer = GroupWelcomeMailer(user=self.user.guid, group=self.group.guid)

    @mock.patch("core.mail_builders.group_welcome.schedule_group_welcome_mail")
    def test_submit_mail(self, mocked_send_welcome_mail):
        self.group.join(self.user)

        self.assertEqual(1, mocked_send_welcome_mail.call_count)
        self.assertDictEqual({'user': self.user,
                              'group': self.group}, mocked_send_welcome_mail.call_args.kwargs)

    @mock.patch("core.mail_builders.group_welcome.schedule_group_welcome_mail")
    def test_not_submit_mail_if_already_member(self, mocked_send_welcome_mail):
        self.group.join(self.member)

        self.assertEqual(0, mocked_send_welcome_mail.call_count)

    @mock.patch("core.mail_builders.base.MailerBase.build_context")
    def test_context_parameter(self, mocked_build_context):
        mocked_build_context.return_value = {}

        context = self.mailer.get_context()

        self.assertEqual(mocked_build_context.call_args.kwargs['user'], self.user)
        self.assertEqual(mocked_build_context.call_count, 1)
        self.assertIn(self.user.name, context['welcome_message'])
        self.assertIn(self.group.name, context['welcome_message'])
        self.assertIn(self.group.url, context['welcome_message'])

    def test_properties(self):
        self.assertEqual(self.user.get_language(), self.mailer.get_language())
        self.assertEqual("email/group_welcome.html", self.mailer.get_template())
        self.assertEqual(self.user, self.mailer.get_receiver())
        self.assertEqual(self.user.email, self.mailer.get_receiver_email())
        self.assertFalse(self.mailer.get_sender())
        self.assertIn(self.group.name, self.mailer.get_subject())

    @mock.patch("core.mail_builders.group_welcome.schedule_group_welcome_mail")
    def test_fail_silently_if_message_is_not_set(self, mocked_send_mail):
        self.group.welcome_message = ""
        self.group.save()

        self.group.join(self.user)
        self.assertFalse(mocked_send_mail.called)

    @mock.patch("core.mail_builders.group_welcome.schedule_group_welcome_mail")
    def test_mail_is_scheduled_though_message_is_empty(self, mocked_send_mail):
        self.group.welcome_message = self.BLANK_HTML
        self.group.save()

        self.group.join(self.user)
        self.assertTrue(mocked_send_mail.called)

    def test_fail_silently_if_message_is_empty(self):
        self.group.welcome_message = self.BLANK_HTML
        self.group.save()
        self.mailer.group.refresh_from_db()

        try:
            self.mailer.get_context()
            self.fail("unexpectedly did not fail though the message is empty")
        except self.mailer.FailSilentlyError:
            pass
