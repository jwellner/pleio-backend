from unittest import mock

from core.resolvers.query_meetings import first_of_next_month, glue_date_time
from core.tests.helpers import PleioTenantTestCase

from django.utils import timezone


class TestResolveQueryAppointmentTimesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.query = """
        query FetchAppointmentTimes($agendaId: String!
                                    $appointmentTypeId: String!
                                    $startDate: DateTime,
                                    $endDate: DateTime) {
            data: appointmentTimes( agendaId: $agendaId
                                    appointmentTypeId: $appointmentTypeId
                                    startDate: $startDate
                                    endDate: $endDate) {
                day
                times {
                    startDateTime
                    endDateTime
                }
            }
        }
        """
        self.variables = {
            'agendaId': '1',
            'appointmentTypeId': "1000",
            'startDate': None,
            'endDate': None,
        }
        self.override_config(ONLINEAFSPRAKEN_ENABLED=True)

    def test_query_slots_when_it_is_disabled(self):
        self.override_config(ONLINEAFSPRAKEN_ENABLED=False)
        with self.assertGraphQlError("meetings_not_enabled"):
            self.graphql_client.post(self.query, self.variables)

    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_bookable_times')
    def test_without_parameters(self, get_bookable_times):
        result = self.graphql_client.post(self.query, self.variables)
        self.assertEqual(result['data']['data'], [])

    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_bookable_times')
    def test_with_result(self, get_bookable_times):
        get_bookable_times.return_value = [
            {"Date": "2020-02-02",
             "StartTime": "09:00", "EndTime": "10:00",
             "Timestamp": glue_date_time("2020-02-02", "09:00").timestamp()},
            {"Date": "2020-02-02",
             "StartTime": "10:00", "EndTime": "11:00",
             "Timestamp": glue_date_time("2020-02-02", "10:00").timestamp()},
            {"Date": "2020-02-03",
             "StartTime": "09:00", "EndTime": "10:00",
             "Timestamp": glue_date_time("2020-02-03", "09:00").timestamp()},
            {"Date": "2020-02-03",
             "StartTime": "10:00", "EndTime": "11:00",
             "Timestamp": glue_date_time("2020-02-03", "10:00").timestamp()},
        ]
        result = self.graphql_client.post(self.query, self.variables)
        self.assertEqual(result['data']['data'][0]['day'], "2020-02-02T00:00:00+01:00")
        self.assertEqual(result['data']['data'][0]['times'], [
            {'startDateTime': '2020-02-02T09:00:00+01:00', 'endDateTime': '2020-02-02T10:00:00+01:00'},
            {'startDateTime': '2020-02-02T10:00:00+01:00', 'endDateTime': '2020-02-02T11:00:00+01:00'},
        ])
        self.assertEqual(result['data']['data'][1]['day'], "2020-02-03T00:00:00+01:00")
        self.assertEqual(result['data']['data'][1]['times'], [
            {'startDateTime': '2020-02-03T09:00:00+01:00', 'endDateTime': '2020-02-03T10:00:00+01:00'},
            {'startDateTime': '2020-02-03T10:00:00+01:00', 'endDateTime': '2020-02-03T11:00:00+01:00'},
        ])

    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_bookable_times')
    def test_with_parameters(self, get_bookable_times):
        get_bookable_times.return_value = []

        self.variables['startDate'] = "2020-02-02 10:10"
        result = self.graphql_client.post(self.query, self.variables)
        self.assertEqual(result['data']['data'], [])

        self.assertEqual(get_bookable_times.call_args.kwargs, {
            "AgendaId": "1",
            "AppointmentTypeId": "1000",
            "Date": "2020-02-02",
            "EndDate": "2020-04-01",
        })


class TestAppointmentFunctionsTestCase(PleioTenantTestCase):

    def first_of_next_month(self, year, month, day, hour, minutes, seconds=0, microseconds=0):
        spec = timezone.datetime(year=year, month=month, day=day, hour=hour, tzinfo=timezone.utc,
                                 minute=minutes, second=seconds, microsecond=microseconds)
        return first_of_next_month(spec).strftime('%Y-%m-%d %H:%M:%S.%f')

    def test_first_of_next_month_method(self):
        self.assertEqual('2020-04-01 12:00:00.000000', self.first_of_next_month(2020, 2, 2, 2, 2, 2, 2))
        self.assertEqual('2021-01-01 12:00:00.000000', self.first_of_next_month(2020, 11, 2, 2, 2, 2, 2))
        self.assertEqual('2021-02-01 12:00:00.000000', self.first_of_next_month(2020, 12, 11, 2, 2, 2, 2))
        self.assertEqual('2021-02-01 12:00:00.000000', self.first_of_next_month(2020, 12, 11, 22, 2, 2, 2))
        self.assertEqual('2021-02-01 12:00:00.000000', self.first_of_next_month(2020, 12, 22, 22, 22, 2, 2))
        self.assertEqual('2021-02-01 12:00:00.000000', self.first_of_next_month(2020, 12, 31, 22, 22, 22, 2))
        self.assertEqual('2021-02-01 12:00:00.000000', self.first_of_next_month(2020, 12, 31, 22, 22, 22, 2222))
        self.assertEqual('2021-02-01 12:00:00.000000', self.first_of_next_month(2020, 12, 31, 0, 0, 0, 0))
