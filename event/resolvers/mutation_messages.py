from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, NOT_AUTHORIZED
from core.lib import clean_graphql_input, NumberIncrement
from event.mail_builders.custom_message import submit_send_event_message
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

        default_kwargs = {
            'event': event.guid,
            'sender': user.guid,
            'message': clean_input.get('message'),
            'subject': clean_input.get('subject'),
        }

        message_count = NumberIncrement()
        for receiving_user in receiving_users:
            mailer_kwargs = default_kwargs.copy()
            mailer_kwargs.update(copy=False, mail_info=receiving_user)
            submit_send_event_message(kwargs=mailer_kwargs,
                                      delay=receiving_user['email'] != user.email)
            message_count.next()

        if clean_input.get('sendCopyToSender', False) and user.email not in attendee_mail:
            mailer_kwargs = default_kwargs.copy()
            mailer_kwargs.update(copy=True, mail_info=user.as_mailinfo())
            submit_send_event_message(kwargs=mailer_kwargs,
                                      delay=False)
            message_count.next()

        return {'success': True,
                'messageCount': message_count.n}

    except Event.DoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)
