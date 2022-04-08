import csv
import io
from core.lib import datetime_isoformat
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.utils.text import slugify
from event.models import Event

class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def export(request, event_id=None):
    # TODO: add check if setting for exporting is set
    # TODO: add tests
    user = request.user

    if not user.is_authenticated:
        raise Http404("Event not found")

    try:
        event = Event.objects.get(id=event_id)
    except ObjectDoesNotExist:
        raise Http404("Event not found")

    if not event.can_write(user):
        raise Http404("Event not found")

    headers = ['guid', 'name', 'email', 'status', 'datetime']
    rows = [headers]
    for attendee in event.attendees.all():
        if attendee.user:
            email = attendee.user.email
        else:
            email = attendee.email
        if attendee.user:
            guid = attendee.user.guid
            name = attendee.user.name
        else:
            guid = ''
            name = attendee.name

        rows.append([guid, name, email, attendee.state, datetime_isoformat(attendee.updated_at)])

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
    writer.writerow(headers)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
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