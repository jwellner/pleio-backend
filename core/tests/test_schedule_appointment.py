from copy import deepcopy

from django.utils import timezone
from unittest import mock

from core import override_local_config
from core.lib import early_this_morning
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestScheduleAppointmentTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.admin = AdminFactory()
        self.mutation = """
        mutation ScheduleAppointment($input: ScheduleAppointmentInput!) {
            scheduleAppointment(input: $input) {
                success
            }
        }
        """
        self.schedule_date = early_this_morning() + timezone.timedelta(hours=10)
        self.variables = {
            "input": {
                "agendaId": "100",
                "appointmentTypeId": "1000",
                "startDateTime": str(self.schedule_date),
                "endDateTime": str(early_this_morning() + timezone.timedelta(hours=11)),
                "attendee": {
                    "email": "mail@example.com",
                    "firstName": "Mister",
                    "lastName": "Test",
                    "phone": "+31698754321"
                }
            }
        }
        self.override_config(ONLINEAFSPRAKEN_ENABLED=True)
        self.override_config(VIDEOCALL_ENABLED=True)

        self.password = self.create_uuid()
        self.uuid4 = mock.patch('uuid.uuid4').start()
        self.uuid4.return_value = self.password

        self.get_customers = mock.patch('core.resolvers.mutation_schedule_appointment.MeetingsApi.get_customers').start()
        self.get_customers.return_value = []
        self.set_customer = mock.patch('core.resolvers.mutation_schedule_appointment.MeetingsApi.set_customer').start()
        self.set_customer.return_value = {'Id': '10'}
        self.set_appointment = mock.patch('core.resolvers.mutation_schedule_appointment.MeetingsApi.set_appointment').start()

    @staticmethod
    def create_uuid():
        from uuid import uuid4
        return uuid4()

    @override_local_config(ONLINEAFSPRAKEN_ENABLED=False)
    def test_error_message_when_not_enabled(self):
        with self.assertGraphQlError("meetings_not_enabled"):
            self.graphql_client.post(self.mutation, self.variables)

    def test_appointment_constraints_non_user_as_non_user(self):
        with self.assertGraphQlError("missing_required_field:attendee.firstName"):
            variables = deepcopy(self.variables)
            variables['input']['attendee']['firstName'] = ''
            self.graphql_client.post(self.mutation, variables)

        with self.assertGraphQlError("missing_required_field:attendee.lastName"):
            variables = deepcopy(self.variables)
            variables['input']['attendee']['lastName'] = ''
            self.graphql_client.post(self.mutation, variables)

        with self.assertGraphQlError("missing_required_field:attendee.email"):
            variables = deepcopy(self.variables)
            variables['input']['attendee']['email'] = ''
            self.graphql_client.post(self.mutation, variables)

        with self.assertGraphQlError("invalid_email"):
            variables = deepcopy(self.variables)
            variables['input']['attendee']['email'] = 'localhost'
            self.graphql_client.post(self.mutation, variables)

    def test_signup_without_videocall(self):
        result = self.graphql_client.post(self.mutation, self.variables)

        self.assertEqual(result['data']['scheduleAppointment']['success'], True)
        self.assertDictEqual(self.get_customers.call_args.kwargs, {
            "Email": self.variables['input']['attendee']['email']
        })
        self.assertDictEqual(self.set_customer.call_args.kwargs, {
            "Username": self.variables['input']['attendee']['email'],
            "Password": self.password,
            "Email": self.variables['input']['attendee']['email'],
            "FirstName": self.variables['input']['attendee']['firstName'],
            "LastName": self.variables['input']['attendee']['lastName'],
            "Phone": self.variables['input']['attendee']['phone'],
        })
        self.assertDictEqual(self.set_appointment.call_args.kwargs, {
            "AgendaId": self.variables['input']['agendaId'],
            "CustomerId": "10",
            "AppointmentTypeId": self.variables['input']['appointmentTypeId'],
            "Date": self.schedule_date.strftime("%Y-%m-%d"),
            "StartTime": '10:00',
            "EndTime": '11:00',
        })

    def test_signup_with_videocall_requires_videocall_enabled(self):
        self.override_config(VIDEOCALL_APPOINTMENT_TYPE=[{"id": "1000", "hasVideocall": True}])
        self.override_config(VIDEOCALL_ENABLED=False)

        with self.assertGraphQlError("videocall_not_enabled"):
            self.graphql_client.post(self.mutation, self.variables)

    @mock.patch('core.resolvers.mutation_schedule_appointment.get_video_call_params')
    def test_signup_with_videocall(self, get_video_call_params):
        get_video_call_params.return_value = {
            "Foo": "Bar",
            "Baz": "Test123"
        }
        self.override_config(VIDEOCALL_APPOINTMENT_TYPE=[{"id": "1000", "hasVideocall": True}])

        result = self.graphql_client.post(self.mutation, self.variables)

        self.assertEqual(get_video_call_params.call_count, 1)
        set_appointment_kwargs = self.set_appointment.call_args.kwargs
        get_video_call_kwargs = get_video_call_params.call_args.args[0]

        self.assertEqual(result['data']['scheduleAppointment']['success'], True)
        self.assertDictEqual(get_video_call_kwargs, {
            "date": self.schedule_date.strftime("%Y-%m-%d"),
            "first_name": self.variables['input']['attendee']['firstName'],
            "last_name": self.variables['input']['attendee']['lastName'],
            "start_time": "10:00",
        })
        self.assertDictEqual(set_appointment_kwargs, {
            "AgendaId": self.variables['input']['agendaId'],
            "CustomerId": "10",
            "AppointmentTypeId": self.variables['input']['appointmentTypeId'],
            "Date": self.schedule_date.strftime("%Y-%m-%d"),
            "StartTime": '10:00',
            "EndTime": '11:00',
            "Foo": "Bar",
            "Baz": "Test123",
        })
