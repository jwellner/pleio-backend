from unittest import mock

from core.factories import GroupFactory
from core.mail_builders.group_membership_approved import GroupMembershipApprovedMailer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestGroupMembershipApprovedMailerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory(email="wannabemember@example.com")
        self.owner = UserFactory(email="owner@example.com")
        self.group = GroupFactory(owner=self.owner)

        self.mailer = GroupMembershipApprovedMailer(user=self.user.guid, group=self.group.guid)

        self.query = """
        mutation ApproveMembership($input: acceptMembershipRequestInput!){
            acceptMembershipRequest(input: $input) {
                group {
                    guid
                }
            }
        }
        """

        self.variables = {
            'input': {
                'userGuid': self.user.guid,
                'groupGuid': self.group.guid,
            }
        }

    @mock.patch('core.mail_builders.group_membership_approved.submit_group_membership_approved_mail')
    def test_submit_approve_membership_mail(self, mocked_send_mail):
        self.graphql_client.force_login(self.owner)
        self.graphql_client.post(self.query, self.variables)

        self.assertEqual(mocked_send_mail.call_count, 1)
        self.assertDictEqual(mocked_send_mail.call_args.kwargs, {
            'group': self.group,
            'user': self.user,
        })

    @mock.patch("core.models.mail.MailInstanceManager.submit")
    def test_schedule_approve_membership_mail(self, mocked_submit_mail):
        mocked_submit_mail.reset_mock()
        self.graphql_client.force_login(self.owner)
        self.graphql_client.post(self.query, self.variables)

        # the submit method of MailInstanceManager may be called more times.
        calls = [c.kwargs for c in mocked_submit_mail.mock_calls if len(c.args) > 0 and c.args[0] == GroupMembershipApprovedMailer]

        self.assertEqual(len(calls), 1)
        self.assertDictEqual(calls[0], {
            'mailer_kwargs': {
                'group': self.group.guid,
                'user': self.user.guid
            }
        })

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mailer_context(self, mocked_build_context):
        mocked_build_context.return_value = {}

        context = self.mailer.get_context()

        self.assertTrue(mocked_build_context.called)
        self.assertDictEqual(mocked_build_context.call_args.kwargs, {
            'user': self.user,
        })
        self.assertEqual(context['group_name'], self.group.name)
        self.assertIn(self.group.url, context['link'])

    def test_mailer_properties(self):
        self.assertEqual(self.mailer.get_language(), self.user.get_language())
        self.assertEqual(self.mailer.get_template(), 'email/accept_membership_request.html')
        self.assertEqual(self.mailer.get_receiver(), self.user)
        self.assertEqual(self.mailer.get_receiver_email(), self.user.email)
        self.assertEqual(self.mailer.get_sender(), None)
        self.assertIn(self.group.name, self.mailer.get_subject())
