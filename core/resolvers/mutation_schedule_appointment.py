import uuid

from graphql import GraphQLError
from online_planner.exceptions import BackendResponseContentError
from online_planner.video_call import get_video_call_params
from online_planner.meetings_api import MeetingsApi, expect_one
from pyisemail import is_email

from core import constances
from core.resolvers import shared


def resolve_mutation_schedule_appointment(obj, info, **kwargs):
    # pylint: disable=unused-argument
    try:
        appointmentDetails = kwargs['input']
        shared.assert_meetings_enabled()
        connection = MeetingsApi()

        attendee = appointmentDetails.get('attendee')
        assert_valid_unknown_attendee(attendee)

        set_customer_kwargs = dict(Email=attendee['email'],
                                   FirstName=attendee['firstName'],
                                   LastName=attendee['lastName'])
        if 'phone' in attendee:
            set_customer_kwargs['Phone'] = attendee['phone']

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

        customer = connection.set_customer(**update_kwargs)

        startDateTime, endDateTime = appointmentDetails.get("startDateTime"), appointmentDetails.get("endDateTime")

        kwargs = dict(AgendaId=appointmentDetails['agendaId'],
                      CustomerId=customer['Id'],
                      AppointmentTypeId=appointmentDetails['appointmentTypeId'],
                      Date=startDateTime.strftime("%Y-%m-%d"),
                      StartTime=startDateTime.strftime("%H:%M"))
        if endDateTime:
            kwargs['EndTime'] = endDateTime.strftime("%H:%M")

        if appointmentDetails.get('includeVideoCall'):
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
        raise GraphQLError(e)


def assert_valid_unknown_attendee(attendee: dict):
    if not attendee.get('firstName'):
        raise GraphQLError(constances.MISSING_REQUIRED_FIELD % 'attendee.firstName')

    if not attendee.get("lastName"):
        raise GraphQLError(constances.MISSING_REQUIRED_FIELD % 'attendee.lastName')

    if not attendee.get("email"):
        raise GraphQLError(constances.MISSING_REQUIRED_FIELD % 'attendee.email')

    if not is_email(attendee.get('email')):
        raise GraphQLError(constances.INVALID_EMAIL)
