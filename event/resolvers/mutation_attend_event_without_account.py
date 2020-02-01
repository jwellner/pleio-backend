from graphql import GraphQLError
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy
from core.constances import COULD_NOT_FIND, INVALID_EMAIL, EMAIL_ALREADY_USED, EVENT_IS_FULL
from core.lib import remove_none_from_dict, send_mail_multi, get_base_url, generate_code, get_default_email_context
from event.models import Event, EventAttendeeRequest

def resolve_attend_event_without_account(_, info, input):
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument

    clean_input = remove_none_from_dict(input)
    email = clean_input.get("email")

    try:
        event = Event.objects.get(id=clean_input.get("guid"))
    except ObjectDoesNotExist:
        raise GraphQLError(COULD_NOT_FIND)

    if event.max_attendees and event.attendees.filter(state="accept").count() >= event.max_attendees:
        raise GraphQLError(EVENT_IS_FULL)

    try:
        validate_email(email)
    except ValidationError:
        raise GraphQLError(INVALID_EMAIL)

    url = get_base_url(info.context) + '/events/confirm/' + event.guid + '?email=' + email + '&code='
    subject = ugettext_lazy("Confirmation of registration %s" % event.title)

    code = ""
    try:
        code = EventAttendeeRequest.objects.get(email=email, event=event).code
    except ObjectDoesNotExist:
        pass

    if code and clean_input.get("resend") is not True:
        raise GraphQLError(EMAIL_ALREADY_USED)

    if not code:
        code = generate_code()
        EventAttendeeRequest.objects.create(code=code, email=email, event=event)

    link = url + code

    context = get_default_email_context(info.context)
    context['link'] = link
    context['title'] = event.title
    context['location'] = event.location
    context['start_date'] = event.start_date

    email = send_mail_multi(subject, 'email/attend_event_without_account.html', context, [email])
    email.send()

    return {
        "entity": event
    }
