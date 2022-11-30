import logging
import uuid

from graphql import GraphQLError
from online_planner.exceptions import BackendResponseContentError
from online_planner.video_call import get_video_call_params
from online_planner.meetings_api import MeetingsApi, expect_one
from pyisemail import is_email

from core import constances, config
from core.resolvers import shared

logger = logging.getLogger(__name__)


def resolve_mutation_schedule_appointment(obj, info, **kwargs):
    # pylint: disable=unused-argument
    try:
        appointmentDetails = kwargs['input']
        shared.assert_meetings_enabled()
        connection = MeetingsApi()

        attendee = appointmentDetails.get('attendee')
        assert_valid_unknown_attendee(attendee)
        customer = get_or_create_customer(attendee)

        startDateTime, endDateTime = appointmentDetails.get("startDateTime"), appointmentDetails.get("endDateTime")
        kwargs = dict(AgendaId=appointmentDetails['agendaId'],
                      CustomerId=customer['Id'],
                      AppointmentTypeId=appointmentDetails['appointmentTypeId'],
                      Date=startDateTime.strftime("%Y-%m-%d"),
                      StartTime=startDateTime.strftime("%H:%M"))
        if endDateTime:
            kwargs['EndTime'] = endDateTime.strftime("%H:%M")

        has_videocall = {str(s['id']): s['hasVideocall'] for s in config.VIDEOCALL_APPOINTMENT_TYPE or []}
        if has_videocall.get(appointmentDetails['appointmentTypeId']):
            shared.assert_videocall_enabled()
            kwargs.update(get_video_call_params(dict(
                date=startDateTime.strftime("%Y-%m-%d"),
                start_time=startDateTime.strftime("%H:%M"),
                first_name=attendee['firstName'],
                last_name=attendee['lastName']
            )))

        connection.set_appointment(**kwargs)
        return {
            'success': True
        }

    except (BackendResponseContentError, AssertionError) as e:
        raise GraphQLError(str(e))


def assert_valid_unknown_attendee(attendee: dict):
    if not attendee.get('firstName'):
        raise GraphQLError(constances.MISSING_REQUIRED_FIELD % 'attendee.firstName')

    if not attendee.get("lastName"):
        raise GraphQLError(constances.MISSING_REQUIRED_FIELD % 'attendee.lastName')

    if not attendee.get("email"):
        raise GraphQLError(constances.MISSING_REQUIRED_FIELD % 'attendee.email')

    if not is_email(attendee.get('email')):
        raise GraphQLError(constances.INVALID_EMAIL)


def get_or_create_customer(attendee):
    connection = MeetingsApi()

    update_kwargs = dict(
        FirstName=attendee['firstName'],
        LastName=attendee['lastName'],
        Email=attendee['email'])
    if 'phone' in attendee:
        update_kwargs['Phone'] = attendee['phone']

    existing_customer = expect_one(connection.get_customers(Email=attendee['email']))
    if not existing_customer:
        update_kwargs['Username'] = attendee['email']
        update_kwargs['Password'] = uuid.uuid4()
    else:
        update_kwargs['Id'] = existing_customer['Id']

    try:
        return connection.set_customer(**update_kwargs)
    except BackendResponseContentError as e:
        if "Username is already in use" in str(e):
            update_kwargs['Username'] = uuid.uuid4()
            return connection.set_customer(**update_kwargs)
        raise
