from unittest import mock

from django.conf import settings
from django.utils.module_loading import import_string

from core import config
from core.tests.helpers import PleioTenantTestCase


class TestMailSystemTemplateMailerTestCase(PleioTenantTestCase):
    """
    To many mocks? Maybe. But this must be double-checked and should never fail.
    Any change to the mail sender class must be intensional.
    """

    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.get_context')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.get_language')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.get_template')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.get_receiver')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.get_receiver_email')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.get_sender')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.get_subject')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.build_context')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.assert_not_known_inactive_user')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.pre_send')
    @mock.patch('core.mail_builders.template_mailer.translation')
    @mock.patch('core.mail_builders.template_mailer.get_template')
    @mock.patch('core.mail_builders.template_mailer.html_to_text')
    @mock.patch('core.mail_builders.template_mailer.formataddr')
    @mock.patch('core.mail_builders.template_mailer.EmailMultiAlternatives')
    def test_template_mailer_send(self, mocked_EmailMultiAlternatives, mocked_formataddr, mocked_html_to_text,
                                  mocked_get_template, mocked_translation,
                                  pre_send, assert_not_known_inactive_user, build_context, get_subject, get_sender,
                                  get_receiver_email, get_receiver, get_template, get_language, get_context):
        from core.mail_builders.template_mailer import TemplateMailerBase
        get_context.return_value = mock.MagicMock()
        get_language.return_value = mock.MagicMock()
        get_template.return_value = mock.MagicMock()
        get_receiver.return_value = mock.MagicMock()
        get_receiver_email.return_value = mock.MagicMock()
        get_sender.return_value = mock.MagicMock()
        get_subject.return_value = mock.MagicMock()
        build_context.return_value = mock.MagicMock()
        mocked_html_to_text.return_value = mock.MagicMock()
        mocked_formataddr.return_value = mock.MagicMock()
        template_render = mock.MagicMock()
        template_render.render.return_value = mock.MagicMock()
        mocked_get_template.return_value = template_render
        mailer_email = mock.MagicMock()
        mocked_EmailMultiAlternatives.return_value = mailer_email

        mailer = TemplateMailerBase()
        mailer.send()

        self.assertEqual(assert_not_known_inactive_user.call_args.args, (get_receiver_email.return_value,),
                         msg="assert_not_known_inactive_user unexpectedly not called with get_receiver_email result.")
        self.assertEqual(mocked_translation.activate.call_args.args, (get_language.return_value,),
                         msg="translation.activate unexpectedly not called with get_language result.")
        self.assertEqual(mocked_get_template.call_args.args, (get_template.return_value,),
                         msg="get_template unexpectedly not called with get_template result.")
        self.assertEqual(template_render.render.call_args.args, (get_context.return_value,),
                         msg="html_template.render unexpextedly not called with get_context result.")
        self.assertEqual(mocked_html_to_text.call_args.args, (template_render.render.return_value,),
                         msg="html_to_text unexpectedly not called with html_template.render result.")

        self.assertEqual(mocked_formataddr.call_args.args, ((config.NAME, settings.FROM_EMAIL),))

        args = mocked_EmailMultiAlternatives.call_args.args
        kwargs = mocked_EmailMultiAlternatives.call_args.kwargs
        assert len(args) == 0, \
            'Called with positional arguments unexpectedly. Use keyword arguments.'
        assert len(kwargs) == 4, \
            'Kwargs unexpectedly changed. Is the  change intensional? If so: update assertions below.'
        assert kwargs['subject'] is get_subject.return_value, \
            'get_subject result not used unexpectedly. Is this change intensional?'
        assert kwargs['body'] is mocked_html_to_text.return_value, \
            'html_to_text result not used unexpectedly. Is this change intensional?'
        assert kwargs['from_email'] is mocked_formataddr.return_value, \
            'formataddr result not used unexpectedly. Is this change intensional?'
        assert kwargs['to'] == [get_receiver_email.return_value], \
            'get_receiver_email result not used unexpectedly. Is this change intensional?'

        args = mailer_email.attach_alternative.call_args.args
        assert len(args) == 2, 'Called with another set of positional arguments unexpectedly. Is this change intensional?'
        self.assertEqual(args, (template_render.render.return_value, "text/html"))

        assert pre_send.called, \
            "pre_send unexpectedly not called"
        assert pre_send.call_args.args == (mailer_email,), \
            "pre_send not called with mailer object."

        assert mailer_email.send.called, \
            "email.send() unexpectedly not called. Is this change intensional?"
        assert len(mailer_email.send.call_args.args) == 0, \
            "email.send() unexpectedly called with positional arguments. Is this change intensional?"
        assert len(mailer_email.send.call_args.kwargs) == 0, \
            "email.send() unexpectedly called with keyword arguments. Is this change intensional?"

    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.get_receiver_email')
    @mock.patch('core.mail_builders.template_mailer.TemplateMailerBase.assert_not_known_inactive_user')
    def test_known_inactive_user_isnt_caught(self, assert_not_known_inactive_user, get_receiver_email):
        expected_exception_class = import_string('core.mail_builders.base.MailerBase').IgnoreInactiveUserMailError
        assert_not_known_inactive_user.side_effect = expected_exception_class("Known inactive user")
        from core.mail_builders.template_mailer import TemplateMailerBase

        mailer = TemplateMailerBase()

        with self.assertRaises(expected_exception_class):
            mailer.send()

        assert assert_not_known_inactive_user.called, "assert_not_known_inactive_user not called unexpectedly. Is this change intensional?"
