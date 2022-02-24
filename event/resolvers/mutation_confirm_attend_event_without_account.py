from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy
from core.constances import COULD_NOT_FIND, INVALID_EMAIL, EVENT_INVALID_STATE, EVENT_IS_FULL, COULD_NOT_SAVE
from core.lib import remove_none_from_dict, get_base_url, get_default_email_context
from event.models import Event, EventAttendeeRequest, EventAttendee
from event.lib import get_url
from core.tasks import send_mail_multi
from django_tenants.utils import parse_tenant_config_path

def resolve_confirm_attend_event_without_account(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument
    clean_input = remove_none_from_dict(input)

    email = clean_input.get("email")
    delete = clean_input.get("delete")
    #TODO: set default value for backwards compatibility, remove if frontend is altered
    state = clean_input.get("state", "accept")

    if state not in ["accept", "reject", "maybe", "waitinglist"]:
        raise GraphQLError(EVENT_INVALID_STATE)

    try:
        event = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    try:
        validate_email(email)
    except ValidationError:
        raise GraphQLError(INVALID_EMAIL)

    try:
        attendee_request = EventAttendeeRequest.objects.get(email=email, code=clean_input.get("code"), event=event)
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if not event.attend_event_without_account:
        raise GraphQLError(COULD_NOT_SAVE)

    # delete attendee and attendee request
    if delete:
        try:
            EventAttendee.objects.get(event=event, email=email).delete()
        except ObjectDoesNotExist:
            raise GraphQLError(COULD_NOT_FIND)
        attendee_request.delete()

    # create attendee
    else:   
        try:
            attendee = event.attendees.get(email=email)
        except ObjectDoesNotExist:
            attendee = None

        if not attendee:
            attendee = EventAttendee()
            attendee.name = attendee_request.name
            attendee.event = event
            attendee.email = email

        if state == "accept":
            if event.is_full():
                raise GraphQLError(EVENT_IS_FULL)

        attendee.state = state
        attendee.save()

        leave_url = get_base_url() + '/events/confirm/' + event.guid + '?email=' + email + '&code='
        leave_link = leave_url + attendee_request.code + '&delete=true'
        
        link = get_url(event, info.context["request"])
        subject = ugettext_lazy("Confirmation of registration for %s") % event.title

        schema_name = parse_tenant_config_path("")
        context = get_default_email_context()
        context['link'] = link
        context['leave_link'] = leave_link
        context['title'] = event.title
        context['location'] = event.location
        context['start_date'] = event.start_date
        context['state'] = state

        send_mail_multi.delay(schema_name, subject, 'email/confirm_attend_event_without_account.html', context, email)

        if state != "accept":
            event.process_waitinglist()

    return {
        "entity": event
    }
