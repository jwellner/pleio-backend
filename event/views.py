import csv
import io
import qrcode

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils import timezone, translation
from django.utils.text import slugify

from core.lib import generate_code, get_base_url
from core.models import Entity
from event.export import AttendeeExporter
from event.models import EventAttendee, Event


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def export(request, event_id=None):
    # pylint: disable=too-many-branches
    user = request.user

    if not user.is_authenticated:
        raise Http404("Not found")

    try:
        event = Event.objects.get(id=event_id)
    except (ObjectDoesNotExist, ValidationError):
        raise Http404("Not found")

    if not event.can_write(user):
        raise Http404("Not found")

    event_export = AttendeeExporter(event, user)

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
    response = StreamingHttpResponse((writer.writerow(row) for row in event_export.rows()),
                                     content_type="text/csv")
    filename = slugify(event.title)
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'

    return response


def export_calendar(request):
    output = io.StringIO()
    output.write('BEGIN:VCALENDAR\n')
    output.write('VERSION:2.0\n')
    output.write('BEGIN:VEVENT\n')
    output.write('DTSTART:' + request.GET.get("startDate", "") + '\n')
    output.write('DTEND:' + request.GET.get("endDate", "") + '\n')
    output.write('SUMMARY:' + request.GET.get("text", "") + '\n')
    output.write('URL:' + request.GET.get("url", "") + '\n')
    output.write('DESCRIPTION:' + request.GET.get("details", "") + '\n')
    if request.GET.get("location", ""):
        output.write('LOCATION:' + request.GET.get("location", "") + '\n')
    elif request.GET.get("locationAddress", ""):
        output.write('LOCATION:' + request.GET.get("locationAddress", "") + '\n')
    output.write('END:VEVENT\n')
    output.write('END:VCALENDAR\n')

    response = HttpResponse(output.getvalue(), content_type="text/calendar; charset=utf-8")
    output.close()
    filename = slugify(request.GET.get("text", "event"))
    response['Content-Disposition'] = f'attachment; filename="{filename}.ics"'
    return response


def get_access_qr(request, entity_id, email=None):
    if request.user:
        user = request.user
        if not user.is_authenticated:
            raise Http404("Event not found")

        try:
            entity = Entity.objects.visible(user).get_subclass(id=entity_id)
        except ObjectDoesNotExist:
            raise Http404("Event not found")

    if email is None:
        attendee = EventAttendee.objects.get(user=user, event=entity)
    else:
        attendee = EventAttendee.objects.get(email=email, event=entity)

    if hasattr(entity, 'title') and entity.title:
        filename = slugify(entity.title)[:238].removesuffix("-")
    else:
        filename = entity.id
    filename = f"qr_access_{filename}.png"

    code = ""
    try:
        code = attendee.code
    except ObjectDoesNotExist:
        pass

    if not code:
        code = generate_code()
        EventAttendee.code = code

    url = get_base_url() + "/events/view/guest-list?code={}".format(code)

    qr_code = qrcode.make(url)

    response = HttpResponse(content_type='image/png')
    qr_code.save(response, "PNG")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


def check_in(request):
    user = request.user

    try:
        attendee = EventAttendee.objects.get(code=request.GET.get('code'))
    except EventAttendee.DoesNotExist:
        raise Http404("Attendee not found")

    event = Event.objects.get(id=attendee.event.guid)

    if event.owner != user:
        raise Http404("Not event owner")

    context = {
        'next': request.GET.get('next', ''),
        'name': attendee.user.name,
        'email': attendee.user.email,
        'check_in': attendee.checked_in_at,
        'event': event.title,
        'date': event.start_date
    }

    if request.method == 'POST':
        attendee.checked_in_at = timezone.now()
        attendee.save()
        return render(request, 'check_in/checked_in.html', context)

    if attendee.checked_in_at is None:
        return render(request, 'check_in/check_in.html', context)

    return render(request, 'check_in/already_checked_in.html', context)
