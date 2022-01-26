from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy
from core.constances import COULD_NOT_FIND, NOT_LOGGED_IN, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, get_default_email_context
from user.models import User
from event.models import Event
from event.lib import get_url
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_delete_event_attendees(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument

    user = info.context["request"].user

    clean_input = remove_none_from_dict(input)

    if not info.context["request"].user.is_authenticated:
        raise GraphQLError(NOT_LOGGED_IN)

    try:
        event = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not event.can_write(user):
        raise GraphQLError(COULD_NOT_SAVE)

    link = get_url(event, info.context["request"])
    subject = ugettext_lazy("Removed from event: %s") % event.title

    for email_address in clean_input.get("emailAddresses"):
        if event.delete_attendee(user, email_address):
            schema_name = parse_tenant_config_path("")
            context = get_default_email_context()
            context['link'] = link
            context['title'] = event.title
            context['removed_attendee_name']  = None
            try:
                context['removed_attendee_name'] = User.objects.get(email=email_address).name
            except ObjectDoesNotExist:
                pass
            send_mail_multi.delay(schema_name, subject, 'email/delete_event_attendees.html', context, email_address)

    return {
        "entity": event
    }
