import logging

from django.db import models
from django.utils import timezone
from django.utils.module_loading import import_string

from core.lib import tenant_schema
from core.mail_builders.base import MailerBase, assert_valid_mailer_subclass

logger = logging.getLogger(__name__)


class MailInstanceManager(models.Manager):

    def submit(self, mailer, mailer_kwargs, delay=True):
        assert_valid_mailer_subclass(mailer)

        instance = self.create(mailer=mailer.class_id(),
                               mailer_kwargs=mailer_kwargs)

        from core.tasks import send_mail_by_instance
        if delay:
            send_mail_by_instance.delay(tenant_schema(), instance.id)
        else:
            send_mail_by_instance(tenant_schema(), instance.id)

        return instance


class MailInstance(models.Model):
    objects = MailInstanceManager()
    error = None

    scheduled_at = models.DateTimeField(default=timezone.localtime)

    mailer = models.CharField(max_length=255)
    mailer_kwargs = models.JSONField()

    def _build_mailer(self) -> MailerBase:
        mailer_class = import_string(self.mailer)
        return mailer_class(**self.mailer_kwargs)

    def send(self):
        mailer: MailerBase = self._build_mailer()

        try:
            self.error = None
            result = mailer.send()
        except MailerBase.IgnoreInactiveUserMailError:
            return
        except Exception as e:
            self.error = e
            result = {
                'error': str(e),
                'error_type': str(e.__class__),
            }

        MailLog.objects.create(
            subject=mailer.get_subject(),
            sender=mailer.get_sender(),
            receiver=mailer.get_receiver(),
            receiver_email=mailer.get_receiver_email(),
            mail_instance=self,
            result=result
        )


def load_mailinstance(pk):
    return MailInstance.objects.get(id=pk)


class MailLog(models.Model):
    created_at = models.DateTimeField(default=timezone.localtime)

    sender = models.ForeignKey('user.User', null=True, on_delete=models.CASCADE, related_name='mails_sent_by_me')

    receiver = models.ForeignKey('user.User', null=True, on_delete=models.CASCADE, related_name='mails_send_to_me')
    receiver_email = models.EmailField()

    subject = models.CharField(max_length=255)
    mail_instance = models.ForeignKey('core.MailInstance', null=True, on_delete=models.CASCADE)
    result = models.JSONField(null=True, blank=True)
