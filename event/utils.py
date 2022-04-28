
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy
from graphql import GraphQLError

from core.constances import INVALID_EMAIL
from core.lib import generate_code, get_base_url, get_default_email_context, tenant_schema
from core.tasks.mail_tasks import send_mail_multi_with_qr_code
from event.lib import get_url


def send_event_qr(info, email, event, attendee):
    try:
        validate_email(email)
    except ValidationError:
        raise GraphQLError(INVALID_EMAIL)

    link = get_url(event, info.context["request"])

    subject = ugettext_lazy("QR code for %s") % event.title
    context = get_default_email_context()
    context['title'] = event.title
    context['location'] = event.location
    context['locationAddress'] = event.location_address
    context['locationLink'] = event.location_link
    context['startDate'] = event.start_date
    context['link'] = link

    if hasattr(event, 'title') and event.title:
        file_name = slugify(event.title)[:238].removesuffix("-")
    else:
        file_name = event.id
    file_name = f"qr_access_{file_name}.png"

    try:
        code = attendee.code
    except ObjectDoesNotExist:
        code = ""

    if not code:
        code = generate_code()
        attendee.code = code
        attendee.save()

    url = get_base_url() + "/events/view/guest-list?code={}".format(code)

    send_mail_multi_with_qr_code.delay(tenant_schema(), subject, 'email/attend_event_with_qr_access.html', context, email, file_name, url)
