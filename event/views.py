import csv
import io
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse, StreamingHttpResponse
from event.models import Event
from core.constances import USER_ROLES

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

    headers = ['guid', 'name', 'email (only for admins)', 'status', 'datetime']
    rows = [headers]
    for attendee in event.attendees.all():
        if user.has_role(USER_ROLES.ADMIN):
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

        rows.append([guid, name, email, attendee.state, attendee.updated_at])

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer, delimiter=';', quotechar='"')
    writer.writerow(headers)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="' + event.title + '.csv"'
    return response


def export_calendar(request):
    output = io.StringIO()
    output.write('BEGIN:VCALENDAR\n')
    output.write('VERSION:2.0\n')
    output.write('BEGIN:VTIMEZONE\n')
    output.write('TZID:Europe/Amsterdam\n')
    output.write('END:VTIMEZONE\n')
    output.write('BEGIN:VEVENT\n')
    output.write('DTSTART;TZID=Europe/Amsterdam:' + request.GET.get("startDate") + '\n')
    output.write('DTEND;TZID=Europe/Amsterdam:' + request.GET.get("endDate") + '\n')
    output.write('SUMMARY:' + request.GET.get("text") + '\n')
    output.write('URL:' + request.GET.get("url") + '\n')
    output.write('DESCRIPTION:' + request.GET.get("details") + '\n')
    output.write('LOCATION:' + request.GET.get("location") + '\n')
    output.write('END:VEVENT\n')
    output.write('END:VCALENDAR\n')

    response = HttpResponse(output.getvalue(), content_type="text/calendar; charset=utf-8")
    output.close()
    response['Content-Disposition'] = 'attachment; filename="event.ics"'
    return response
