import faker

from unittest import mock

from django.utils.module_loading import import_string

from core.lib import tenant_schema
from core.models import MailInstance
from core.tests.helpers import PleioTenantTestCase


class TestMailSystemTestCase(PleioTenantTestCase):

    @mock.patch('core.tasks.send_mail_by_instance')
    def test_submit_should_accept_valid_subclass(self, mocked_send_mail_by_instance):
        from core.models import MailInstance
        from core.tests.helpers_mailer_subclasses import InvalidMailerSubclass

        with self.assertRaises(AssertionError):
            MailInstance.objects.submit(InvalidMailerSubclass, {})

    @mock.patch('core.tasks.send_mail_by_instance')
    def test_submit_should_create_a_mail_instance_object(self, mocked_send_mail_by_instance):
        from core.models import MailInstance
        from core.tests.helpers_mailer_subclasses import ValidMailerSubclass

        instance = MailInstance.objects.submit(ValidMailerSubclass, {})

        assert instance.id, 'should have set an id'
        assert instance.mailer, 'should have set a mailer'

    @mock.patch('core.tasks.send_mail_by_instance')
    def test_submit_should_schedule_the_instance(self, mocked_send_mail_by_instance):
        from core.models import MailInstance
        from core.tests.helpers_mailer_subclasses import ValidMailerSubclass

        MailInstance.objects.submit(ValidMailerSubclass, {})

        assert mocked_send_mail_by_instance.delay.called, "has not scheduled the mailer instance"

    @mock.patch('core.tasks.send_mail_by_instance')
    def test_submit_should_execute_the_instance(self, mocked_send_mail_by_instance):
        from core.models import MailInstance
        from core.tests.helpers_mailer_subclasses import ValidMailerSubclass

        MailInstance.objects.submit(ValidMailerSubclass, {}, delay=False)

        assert mocked_send_mail_by_instance.called, "has not executed the mailer instance directly"

    @mock.patch('core.models.mail.load_mailinstance')
    def test_should_call_send_inside_send_mail_by_instance(self, mocked_load_mailinstance):
        from core.models import MailInstance
        from core.tests.helpers_mailer_subclasses import ValidMailerSubclass

        instance = mock.MagicMock(spec=MailInstance)
        mocked_load_mailinstance.return_value = instance

        MailInstance.objects.submit(ValidMailerSubclass, {}, delay=False)

        assert instance.send.called, "did not call 'send' inside send_mail_by_instance"

    @mock.patch('core.tests.helpers_mailer_subclasses.ValidMailerSubclass.send')
    def test_send_should_create_a_log_record(self, mocked_send):
        from core.models import MailInstance, MailLog
        from core.tests.helpers_mailer_subclasses import ValidMailerSubclass

        mocked_send.return_value = {"subject": "Testmail", "body": "Some content."}
        instance = MailInstance.objects.submit(ValidMailerSubclass, {}, delay=False)

        assert mocked_send.called, "did not call send on the mailer object"
        assert MailLog.objects.get(mail_instance=instance), "did not create a log record"

    @mock.patch('core.tests.helpers_mailer_subclasses.ValidMailerSubclass.send')
    def test_send_with_errors_should_create_a_log_record(self, mocked_send):
        from core.models import MailInstance, MailLog
        from core.tests.helpers_mailer_subclasses import ValidMailerSubclass

        ERROR = faker.Faker().sentence()
        mocked_send.side_effect = Exception(ERROR)

        instance = MailInstance.objects.submit(ValidMailerSubclass, {}, delay=False)

        assert mocked_send.called, "did not call send on the mailer object"
        assert MailLog.objects.get(mail_instance=instance), "did not create a log record"

        logrecord = MailLog.objects.get(mail_instance=instance)
        self.assertEqual(logrecord.result['error'], ERROR)
        self.assertEqual(logrecord.result['error_type'], "<class 'Exception'>")

    @mock.patch('core.tests.helpers_mailer_subclasses.ValidMailerSubclass.send')
    def test_send_with_errors_should_add_error_to_celery_log(self, mocked_send):
        from core.tests.helpers_mailer_subclasses import ValidMailerSubclass

        ERROR = faker.Faker().sentence()
        mocked_send.side_effect = Exception(ERROR)

        with mock.patch('core.tasks.mail_tasks.logger') as mocked_logger:
            instance = MailInstance.objects.submit(ValidMailerSubclass, {}, delay=False)

        assert mocked_logger.error.called, "logger.error() unexpectedly not called in mail_tasks.send_mail_by_instance."

        args = mocked_logger.error.call_args.args
        self.assertIn(instance.id, args,
                      msg="Mailer instance not found in errorlog params.")
        self.assertIn(str(mocked_send.side_effect), args,
                      msg="Error message not found in errorlog params.")
        self.assertIn(tenant_schema(), args,
                      msg="Tenant schema not found in errorlog params.")
        self.assertIn(Exception, args,
                      msg="Exception type not found in errorlog params.")
        self.assertIn("background_email_error", args[0],
                      msg="Filter text 'background_email_error' not found in errorlog params")

    @mock.patch('core.tests.helpers_mailer_subclasses.ValidMailerSubclass.send')
    def test_send_to_inactive_user_should_not_add_error_to_celery_log(self, mocked_send):
        from core.tests.helpers_mailer_subclasses import ValidMailerSubclass

        expected_exception_class = import_string('core.mail_builders.base.MailerBase').IgnoreInactiveUserMailError
        mocked_send.side_effect = expected_exception_class()

        with mock.patch('core.tasks.mail_tasks.logger') as mocked_logger:
            MailInstance.objects.submit(ValidMailerSubclass, {}, delay=False)

        assert not mocked_logger.error.called, "logger.error() unexpectedly called in mail_tasks.send_mail_by_instance."
