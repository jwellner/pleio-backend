from graphql import GraphQLError

from core.constances import COULD_NOT_FIND, NOT_AUTHORIZED
from event.models import Event


def resolve_send_message_to_event(_, info, input):
    try:
        event = Event.objects.get(guid=input['guid'])

        user = info.context['request'].user
        if not event.can_write(user):
            raise GraphQLError(NOT_AUTHORIZED)

        # TODO: send mail.

        return {'success': True}

    except Event.DoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    return {'success': False}
