import uuid
from django.conf import settings
from online_planner.online_meetings import online_meetings_get, extract_items_from_xml, online_meetings_put
from online_planner.settings_container import SettingsContainerBase

from core import config


class SettingsContainer(SettingsContainerBase):
    def get_key(self):
        return config.ONLINEAFSPRAKEN_KEY

    def get_secret(self):
        return config.ONLINEAFSPRAKEN_SECRET

    def get_url(self):
        return config.ONLINEAFSPRAKEN_URL or settings.ONLINE_MEETINGS_URL

    def get_video_api_url(self):
        return config.VIDEOCALL_API_URL or settings.VIDEO_CALL_RESERVE_ROOM_URL


class MeetingsApi:
    """
    @see https://onlineafspraken.nl/nl_NL/developers/referentie
    """

    def cancel_appointment(self, **kwargs):
        """
        Accepts:
          - Id
          - Mode [customer*, company]
          - Remarks (When Mode=company)
          - Confirmations (0...3)
          - DryRun (0*, 1)
        """
        assert kwargs.get('Id'), 'Provide an appointment id.'

        online_meetings_put('cancelAppointment', kwargs)

    def confirm_appointment(self, **kwargs):
        """
        Accepts:
          - Id
          - ConfirmationCode
        """
        assert kwargs.get('Id'), 'Provide an appointment id.'
        assert kwargs.get('ConfirmationCode'), 'Provide a confirmation code.'

        online_meetings_put('confirmAppointment', kwargs)

    def get_appointment(self, **kwargs):
        """
        Accepts:
        - Id
        """
        assert kwargs.get('Id'), 'Provide an appointment id.'

        response = online_meetings_get('getAppointment', kwargs)
        return expect_one(extract_items_from_xml('Appointment', response))

    def update_or_create_customer(self, **kwargs):
        user = expect_one(self.get_customers(Email=kwargs['Email']))

        if not user:
            kwargs['Username'] = uuid.uuid4()
            kwargs['Password'] = uuid.uuid4()
            return self.set_customer(**kwargs)



    def get_appointments(self, **kwargs):
        """
        Accepts:
        - AgendaId
        - StartDate
        - EndDate
        - CustomerId
        - AppointmentTypeId
        - ResourceId
        - IncludeCanceled
        - Limit
        - Offset
        - FilterWorkflow
        - Include
        """
        assert kwargs.get('AgendaId'), "Provide an agenda id."
        assert kwargs.get('StartDate'), "Provide a start date."
        assert kwargs.get('EndDate'), "Provide an end date."

        response = online_meetings_get('getAppointments', kwargs)
        return extract_items_from_xml('Appointment', response)

    def remove_appointment(self, **kwargs):
        """
        Accepts:
        - Id
        """
        assert kwargs.get('Id'), 'Provide an appointment id.'

        online_meetings_get('removeAppointment', kwargs)

    def set_appointment(self, **kwargs):
        """
        Accepts:
        - AgendaId*
        - CustomerId*
        - AppointmentTypeId*
        - ResourceId
        - Date*
        - StartTime*
        - EndTime (required if BookingMode=customer)
        - Id (required when changing an existing appointment)
        - Name
        - Description
        - ** (extra fields)
        - BookingMode (consumer*, customer)
        - OverrideMode (1* 0)
        - RequiredFieldsCheck (1*, 0)
        - Referrer
        - AppStatus
        - Confirmations (1*, 0)
        - Notifications(1*, 0)
        """
        assert kwargs.get("AgendaId"), "Provide an agenda id"
        assert kwargs.get("CustomerId"), "Provide a customer id"
        assert kwargs.get("AppointmentTypeId"), "Provide an appointment type id"
        assert kwargs.get("Date"), "Provide a date"
        assert kwargs.get("StartTime"), "Provide a start time"
        if kwargs.get("BookingMode") == 'customer':
            assert kwargs.get("EndTime")

        response = online_meetings_put('setAppointment', kwargs)
        return expect_one(extract_items_from_xml('Appointment', response))

    def get_agenda(self, **kwargs):
        """
        Accepts:
        - AgendaId*
        """
        assert kwargs.get("AgendaId")
        response = online_meetings_get('getAgenda')
        return expect_one(extract_items_from_xml('Agenda', response))

    def get_agendas(self):
        response = online_meetings_get('getAgendas')
        return extract_items_from_xml('Agenda', response)

    def get_appointment_type(self, **kwargs):
        """
        Accepts:
        - Id*
        """
        assert kwargs.get('Id'), "Provide an appointment type id."

        response = online_meetings_get('getAppointmentType', kwargs)
        return expect_one(extract_items_from_xml('AppointmentType', response))

    def get_appointment_types(self):
        response = online_meetings_get('getAppointmentTypes')
        return extract_items_from_xml('AppointmentType', response)

    def get_resource(self, **kwargs):
        """
        Accepts:
        - ResourceId*
        """
        assert kwargs.get("ResourceId"), "Provide a resource id"

        response = online_meetings_get("getResource", kwargs)
        return expect_one(extract_items_from_xml('Resource', response))

    def get_resources(self):
        response = online_meetings_get('getResources')
        return extract_items_from_xml('Resource', response)

    def requires_confirmation(self):
        response = online_meetings_get('requiresConfirmation')
        return expect_one(extract_items_from_xml('Confirmation', response))

    def get_bookable_blocks(self, **kwargs):
        """
        Accepts:
        - AgendaId*
        - AppointmentTypeId*
        - ResourceId
        - Date*
        - EndDate
        - CustomerBookable
        """
        assert kwargs.get("AgendaId"), "Provide an agenda id"
        assert kwargs.get("AppointmentTypeId"), "Provide an appointment type id"
        assert kwargs.get("Date"), "Provide a date"

        response = online_meetings_get("getBookableBlocks", kwargs)
        return extract_items_from_xml("BookableBlock", response)

    def get_bookable_days(self, **kwargs):
        """
        Accepts:
        - AgendaId*
        - AppointmentTypeId*
        - ResourceId
        - StartDate*
        - EndDate*
        """
        assert kwargs.get("AgendaId"), "Provide an agenda id"
        assert kwargs.get("AppointmentTypeId"), "Provide an appointment type id"
        assert kwargs.get("StartDate"), "Provide a start date"
        assert kwargs.get("EndDate"), "Provide a start date"

        response = online_meetings_get("getBookableDays", kwargs)
        return extract_items_from_xml("BookableDay", response)

    def get_bookable_times(self, **kwargs):
        """
        Accepts:
        - AgendaId*
        - AppointmentTypeId*
        - ResourceId
        - Date*
        - EndDate
        """
        assert kwargs.get("AgendaId"), "Provide an agenda id"
        assert kwargs.get("AppointmentTypeId"), "Provide an appointment type id"
        assert kwargs.get("Date"), "Provide a date"

        response = online_meetings_get("getBookableTimes", kwargs)
        return extract_items_from_xml("BookableTime", response)

    def get_customer(self, **kwargs):
        """
        Accepts:
        - Id*
        """
        assert kwargs.get("Id"), "Provide a customer id"

        response = online_meetings_get("getCustomer", kwargs)
        return expect_one(extract_items_from_xml("Customer", response))

    def get_customers(self, **kwargs):
        """
        Accepts:
        - Limit
        - Offset
        - UpdatedAfter
        - Email
        - BirthDate
        - AccountNumber
        """
        response = online_meetings_get("getCustomers", kwargs)
        return extract_items_from_xml("Customer", response)

    def set_customer(self, **kwargs):
        """
        Accepts:
        - Id
        - AccountNumber
        - Email*
        - FirstName*
        - LastName*
        - Insertions
        - BirthDate
        - Gender
        - Street
        - HouseNr
        - HouseNrAddition
        - ZipCode
        - City
        - Country
        - Phone
        - MobilePhone
        - Status
        - [ Variable ]
        - Username
        - Password
        """
        assert kwargs.get('Email'), "Provide a value for Email."
        assert kwargs.get('FirstName'), "Provide a value for FirstName."
        assert kwargs.get('LastName'), "Provide a value for LastName."

        response = online_meetings_put("setCustomer", kwargs)
        return expect_one(extract_items_from_xml("Customer", response))

    def get_fields(self, **kwargs):
        """
        Accepts:
        - AgendaId*
        - AppointmentTypeId*
        - GenericFields (0*, 1)
        """
        assert kwargs.get("AgendaId"), "Provide an agenda id"
        assert kwargs.get("AppointmentTypeId"), "Provide an appointment type id"

        response = online_meetings_get("getFields", kwargs)
        return extract_items_from_xml("Field", response)


def expect_one(items):
    for item in items:
        return item
    return None
