from django.utils import translation
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy
from django_tenants.utils import parse_tenant_config_path
from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, NOT_AUTHORIZED
from core.lib import clean_graphql_input, get_default_email_context, get_base_url
from core.tasks import send_mail_multi
from event.models import Event, EventAttendee


def resolve_send_message_to_event(_, info, input):
    # pylint: disable=redefined-builtin
    try:
        event = Event.objects.get(id=input.get('guid'))

        user = info.context['request'].user
        if not event.can_write(user):
            raise GraphQLError(NOT_AUTHORIZED)

        clean_input = clean_graphql_input(input)

        receiving_users = []
        attendee_mail = []
        if clean_input.get('isTest'):
            receiving_users.append(user.as_mailinfo())
        else:
            if clean_input.get('sendToAttendees'):
                for attendee in EventAttendee.objects.filter(event=event, state='accept'):
                    receiving_users.append(attendee.as_mailinfo())
                    attendee_mail.append(attendee.email)

        messenger = SendEventMessage()
        messenger.populate(event=event,
                           sender=user,
                           message=clean_input.get('message'),
                           subject=clean_input.get('subject'))

        for receiving_user in receiving_users:
            messenger.send(mail_info=receiving_user,
                           copy=False)

        if clean_input.get('sendCopyToSender', False) and user.email not in attendee_mail:
            messenger.send(mail_info=user.as_mailinfo(),
                           copy=True)

        return {'success': True,
                'messageCount': messenger.messageCount}

    except Event.DoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)


class SendEventMessage:

    def __init__(self):
        self.messageCount = 0

    def populate(self, event, sender, message, subject):
        self.event = event
        self.sender = sender
        self.context = get_default_email_context(sender)
        self.schema_name = parse_tenant_config_path("")
        self.context['message'] = format_html(message)
        self.context['event'] = event.title
        self.context['event_url'] = get_base_url() + event.url
        self.subject = subject

    def send(self, mail_info, copy: bool):
        translation.activate(mail_info['language'])
        if not copy:
            subject = ugettext_lazy("Message from event {0}: {1}").format(self.event.title, self.subject)
        else:
            subject = ugettext_lazy("Copy: Message from event {0}: {1}").format(self.event.title, self.subject)

        self.messageCount = self.messageCount + 1

        send_mail_multi.delay(
            schema_name=self.schema_name,
            subject=subject,
            html_template='email/send_message_to_event.html',
            context=self.context,
            email_address=mail_info['email'],
            language=mail_info['language']
        )
