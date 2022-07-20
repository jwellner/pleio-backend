from django.conf import settings
from django.utils.translation import gettext as _

from core.lib import get_full_url
from core.mail_builders.template_mailer import TemplateMailerBase
from core.utils.entity import load_entity_by_id


def submit_delete_event_attendees_mail(event, mail_info, user=None):
    from core.models import MailInstance
    MailInstance.objects.submit(DeleteEventAttendeeMailer, mailer_kwargs={
        'event': event.guid,
        'mail_info': mail_info,
        'user': user.guid if user else None
    }, delay=settings.ENV != 'local')


class DeleteEventAttendeeMailer(TemplateMailerBase):
    def __init__(self, **kwargs):
        super(DeleteEventAttendeeMailer, self).__init__(**kwargs)
        self.mail_info = kwargs['mail_info']
        self.event = load_entity_by_id(kwargs['event'], ['event.Event'])
        self.user = load_entity_by_id(kwargs['user'], ['user.User']) if kwargs['user'] else None

    def get_context(self):
        context = self.build_context()
        context['link'] = get_full_url(self.event.url)
        context['title'] = self.event.title
        context['removed_attendee_name'] = self.mail_info['name']
        return context

    def get_language(self):
        return self.mail_info['language']

    def get_template(self):
        return 'email/delete_event_attendees.html'

    def get_receiver(self):
        return self.user

    def get_receiver_email(self):
        return self.mail_info['email']

    def get_sender(self):
        return None

    def get_subject(self):
        return _("Removed from event: %s") % self.event.title
