from collections import defaultdict

import pytz
from django.utils import timezone
from django.utils.timezone import datetime, localtime, timedelta
from graphql import GraphQLError
from online_planner.exceptions import BackendResponseContentError
from online_planner.meetings_api import MeetingsApi

from core.lib import early_this_morning
from core.resolvers import shared


def resolve_query_appointment_data(*_):
    shared.assert_meetings_enabled()
    try:
        return {
            'agendas': shared.resolve_load_agendas(),
            'appointmentTypes': shared.resolve_load_appointment_types(),
        }
    except (BackendResponseContentError, AssertionError) as e:
        raise GraphQLError(e)


def resolve_query_appointment_times(_, info, agendaId, appointmentTypeId, startDate: datetime = None, endDate: datetime = None):
    # pylint: disable=unused-argument
    shared.assert_meetings_enabled()

    connection = MeetingsApi()
    try:
        if not startDate:
            startDate = localtime()
        if not endDate:
            endDate = first_of_next_month(startDate)

        times = connection.get_bookable_times(AgendaId=agendaId,
                                              AppointmentTypeId=appointmentTypeId,
                                              Date=startDate.strftime("%Y-%m-%d"),
                                              EndDate=endDate.strftime("%Y-%m-%d"))

        result = defaultdict(list)
        for slot in [AppointmentTime(t) for t in times]:
            result[early_this_morning(slot.startDateTime)].append(slot)

        return [{'day': day,
                 'times': times} for day, times in result.items()]
    except (BackendResponseContentError, AssertionError) as e:
        raise GraphQLError(e)


def first_of_next_month(reference: datetime):
    reference -= timedelta(days=(reference.day - 1),
                           hours=reference.hour - 12,
                           minutes=reference.minute,
                           seconds=reference.second,
                           microseconds=reference.microsecond)
    reference += timedelta(days=64)
    reference -= timedelta(days=(reference.day - 1))
    return reference


class AppointmentTime:
    def __init__(self, record):
        self.record = record
        self.start_date_time = None

    @property
    def timestamp(self):
        return int(self.record['Timestamp'])

    @property
    def startDateTime(self) -> timezone.datetime:
        if self.start_date_time is None:
            self.start_date_time = timezone.datetime.fromtimestamp(self.timestamp, pytz.timezone("CET"))
        return self.start_date_time

    @property
    def endDateTime(self) -> timezone.datetime:
        start = glue_date_time(self.record['Date'], self.record['StartTime'])
        end = glue_date_time(self.record['Date'], self.record['EndTime'])
        return self.startDateTime + (end - start)


def glue_date_time(date_string, time_string):
    return datetime.fromisoformat("%s %s" % (date_string, time_string))
