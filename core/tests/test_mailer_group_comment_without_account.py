from unittest import mock

import faker
from mixer.backend.django import mixer

from blog.models import Blog
from core import override_local_config
from core.constances import ACCESS_TYPE
from core.lib import generate_code
from core.mail_builders.comment_without_account import CommentWithoutAccountMailer
from core.models import CommentRequest
from core.tests.helpers import PleioTenantTestCase
from core.utils.convert import tiptap_to_html


class TestGroupCommentWithoutAccountMailer(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.COMMENT = self.tiptap_paragraph(faker.Faker().sentence())

        self.entity = mixer.blend(Blog,
                                  read_access=[ACCESS_TYPE.public])
        self.pending_comment = mixer.blend(CommentRequest,
                                           code=generate_code(),
                                           email=faker.Faker().email(),
                                           rich_description=self.COMMENT)
        self.mailer = CommentWithoutAccountMailer(comment_request=self.pending_comment.pk,
                                                  entity=self.entity.guid)

        self.query = """
        mutation AddComment($input: addCommentWithoutAccountInput!) {
            addCommentWithoutAccount(input: $input) {
                success
            }
        }
        """
        self.EMAIL = faker.Faker().email()
        self.variables = {
            'input': {
                'containerGuid': self.entity.guid,
                'name': faker.Faker().name(),
                'email': self.EMAIL,
                'richDescription': self.COMMENT
            }
        }

    @override_local_config(COMMENT_WITHOUT_ACCOUNT_ENABLED=True)
    @mock.patch("core.mail_builders.comment_without_account.schedule_comment_without_account_mail")
    def test_submit_comment_without_account_mail(self, mocked_send_mail):
        self.graphql_client.post(self.query, self.variables)
        comment_request = CommentRequest.objects.filter(email=self.EMAIL).first()

        self.assertTrue(comment_request)
        self.assertTrue(mocked_send_mail.called_once)
        self.assertDictEqual(mocked_send_mail.call_args.kwargs,
                             {'comment_request': comment_request,
                              'entity': self.entity})

    @override_local_config(COMMENT_WITHOUT_ACCOUNT_ENABLED=True)
    @mock.patch("core.models.mail.MailInstanceManager.submit")
    def test_schedule_comment_without_account_mail(self, mocked_submit_mail):
        self.graphql_client.post(self.query, self.variables)
        comment_request = CommentRequest.objects.filter(email=self.EMAIL).first()

        # the submit method of MailInstanceManager may be called more times.
        calls = [c.kwargs for c in mocked_submit_mail.mock_calls if len(c.args) > 0 and c.args[0] == CommentWithoutAccountMailer]

        self.assertTrue(comment_request)
        self.assertEqual(len(calls), 1)
        self.assertDictEqual(calls[0], {
            'mailer_kwargs': {
                'comment_request': comment_request.pk,
                'entity': self.entity.guid
            }
        })

    @mock.patch('core.mail_builders.base.MailerBase.build_context')
    def test_mailer_context(self, mocked_build_context):
        mocked_build_context.return_value = {}

        context = self.mailer.get_context()
        self.assertIn(self.entity.guid, context['confirm_url'])
        self.assertIn(self.pending_comment.code, context['confirm_url'])
        self.assertIn(self.pending_comment.email, context['confirm_url'])
        self.assertIn(tiptap_to_html(self.COMMENT), context['comment'])
        self.assertEqual(self.entity.title, context['entity_title'])
        self.assertIn(self.entity.url, context['entity_url'])

    @override_local_config(LANGUAGE='zulu')
    @override_local_config(NAME='Foo bar')
    def test_mailer_attributes(self):
        self.assertEqual(self.mailer.get_language(), 'zulu')
        self.assertEqual(self.mailer.get_template(), 'email/confirm_add_comment_without_account.html')
        self.assertEqual(self.mailer.get_receiver(), None)
        self.assertEqual(self.mailer.get_receiver_email(), self.pending_comment.email)
        self.assertEqual(self.mailer.get_sender(), None)
        self.assertIn('Foo bar', self.mailer.get_subject())
