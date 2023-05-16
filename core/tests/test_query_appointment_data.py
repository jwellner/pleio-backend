from unittest import mock

from core.tests.helpers import PleioTenantTestCase, override_config


class TestResolveQueryAppointmentDataTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()
        self.query = """
        query FetchAppointmentData {
            data: appointmentData {
                agendas {
                    id
                    name
                }
                appointmentTypes {
                    id
                    name
                }
            }
        }
        """

    @override_config(ONLINEAFSPRAKEN_ENABLED=False)
    def test_appointments_disabled(self):
        with self.assertGraphQlError("meetings_not_enabled"):
            self.graphql_client.post(self.query, {})

    @override_config(ONLINEAFSPRAKEN_ENABLED=True)
    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_appointment_types')
    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_agendas')
    def test_appointments_enabled(self, get_agendas, get_appointment_types):
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['data']['agendas'], [])
        self.assertEqual(result['data']['data']['appointmentTypes'], [])

    @override_config(ONLINEAFSPRAKEN_ENABLED=True)
    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_appointment_types')
    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_agendas')
    def test_appointments_enabled_with_agendas(self, get_agendas, get_appointment_types):
        get_agendas.return_value = [{"Id": 1, "Name": 'Agenda1'},
                                    {"Id": 2, "Name": "Agenda2"}]
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['data']['agendas'], [{'id': '1', 'name': 'Agenda1'},
                                                             {'id': '2', 'name': 'Agenda2'}])
        self.assertEqual(result['data']['data']['appointmentTypes'], [])

    @override_config(ONLINEAFSPRAKEN_ENABLED=True)
    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_appointment_types')
    @mock.patch('core.resolvers.query_meetings.MeetingsApi.get_agendas')
    def test_appointments_enabled_with_appointment_types(self, get_agendas, get_appointment_types):
        get_appointment_types.return_value = [{"Id": 1, "Name": 'Type1'},
                                              {"Id": 2, "Name": "Type2"}]
        result = self.graphql_client.post(self.query, {})
        self.assertEqual(result['data']['data']['agendas'], [])
        self.assertEqual(result['data']['data']['appointmentTypes'], [{'id': '1', 'name': 'Type1'},
                                                                      {'id': '2', 'name': 'Type2'}])
