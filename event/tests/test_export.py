from unittest import mock

from core.constances import ACCESS_TYPE
from core.factories import GroupFactory
from core.models import ProfileField, GroupProfileFieldSetting, UserProfileField
from core.tests.helpers import PleioTenantTestCase, override_config
from event.factories import EventFactory
from event.models import EventAttendee
from event.export import AttendeeExporter
from user.factories import UserFactory


class TestAttendeeExporterRowsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.event = EventFactory(owner=self.owner,
                                  title="Main event",
                                  rsvp=True)
        self.attendee = EventAttendee.objects.create(event=self.event,
                                                     state='accept',
                                                     user=UserFactory(name="Attendee", email="attendee@example.com"))
        self.sub_event = EventFactory(owner=self.owner,
                                      parent=self.event,
                                      title="Subevent",
                                      rsvp=True)
        self.sub_attendee = EventAttendee.objects.create(event=self.sub_event,
                                                         state='accept',
                                                         user=UserFactory(name="Sub Attendee", email="subatten@example.com"))

        datetime_format = mock.patch("event.export.datetime_format").start()
        datetime_format.return_value = "TIMESTAMP"

    @mock.patch('event.export.AttendeeExporter.maybe_subevent_supplement')
    @mock.patch('event.export.AttendeeExporter.export_subevents')
    @mock.patch('event.export.AttendeeExporter.export_main_event')
    def test_rows(self, export_main, export_sub, export_supp):
        exporter = AttendeeExporter(self.event, self.owner)

        rows = [*exporter.rows()]

        self.assertEqual(rows, [])
        self.assertTrue(export_main.called)
        self.assertTrue(export_sub.called)
        self.assertTrue(export_supp.called)

    def test_main_event_rows(self):
        exporter = AttendeeExporter(self.event, self.owner)

        self.assertEqual([*exporter.rows()], [
            ["Main event", "TIMESTAMP"],
            ["Status", "Bijgewerkt", "Naam", "E-mail"],
            ["Aanvaard", "TIMESTAMP", self.attendee.name, self.attendee.email],
            [],
            ["Subevent", "TIMESTAMP"],
            ["Status", "Bijgewerkt", "Naam", "E-mail"],
            ["Aanvaard", "TIMESTAMP", self.sub_attendee.name, self.sub_attendee.email],
            [],
            ["Alle deelnemers"],
            ['Status', 'Bijgewerkt', 'Naam', 'E-mail', 'Alle evenementen'],
            ['Aanvaard', 'TIMESTAMP', self.attendee.name, self.attendee.email, 'Main event', ''],
            ['Aanvaard', 'TIMESTAMP', self.sub_attendee.name, self.sub_attendee.email, '', 'Subevent'],
        ])

    def test_sub_event_rows(self):
        exporter = AttendeeExporter(self.sub_event, self.owner)
        self.assertEqual([*exporter.rows()], [
            ["Subevent", "TIMESTAMP"],
            ["Status", "Bijgewerkt", "Naam", "E-mail"],
            ["Aanvaard", "TIMESTAMP", self.sub_attendee.name, self.sub_attendee.email],
        ])


class TestExportProfileFieldsTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner)
        self.group_event = EventFactory(title="Group event", owner=self.owner, group=self.group)
        self.site_event = EventFactory(title="Site event", owner=self.owner)

        self.field_free = ProfileField.objects.create(
            key="field_free",
            name="Free field",
            field_type='text_field',
            is_in_overview=True,
            is_mandatory=False)
        self.field_group_mandatory = ProfileField.objects.create(
            key="field_group_mandatory",
            name="Group mandatory field",
            field_type='text_field',
            is_in_overview=True,
            is_mandatory=False)
        self.field_site_mandatory = ProfileField.objects.create(
            key="field_site_mandatory",
            name="Site mandatory field",
            field_type='text_field',
            is_in_overview=True,
            is_mandatory=True)

        self.setting_free_field = GroupProfileFieldSetting.objects.create(
            group=self.group,
            profile_field=self.field_free,
            show_field=True,
            is_required=False,
        )
        self.setting_group_mandatory_field = GroupProfileFieldSetting.objects.create(
            group=self.group,
            profile_field=self.field_group_mandatory,
            show_field=True,
            is_required=True,
        )

        self.user = UserFactory(email="user1@example.com")
        profile_defaults = {"user_profile": self.user.profile,
                            "write_access": [ACCESS_TYPE.user.format(self.user.guid)],
                            "read_access": [ACCESS_TYPE.logged_in]}
        self.profile_free_field_value = UserProfileField.objects.create(
            profile_field=self.field_free,
            value="Free field user1",
            **profile_defaults)
        self.profile_group_mandatory_value = UserProfileField.objects.create(
            profile_field=self.field_group_mandatory,
            value="Group mandatory field user1",
            **profile_defaults)
        self.profile_site_mandatory_value = UserProfileField.objects.create(
            profile_field=self.field_site_mandatory,
            value="Site mandatory field user1",
            **profile_defaults)

        self.group_attendee = EventAttendee.objects.create(
            user=self.user,
            state='accept',
            event=self.group_event,
        )
        self.site_attendee = EventAttendee.objects.create(
            user=self.user,
            state='accept',
            event=self.site_event,
        )
        self.PROFILE_SECTIONS = [{"name": "", "profileFieldGuids": [
            self.field_free.guid,
            self.field_site_mandatory.guid,
            self.field_group_mandatory.guid
        ]}]

        datetime_format = mock.patch("event.export.datetime_format").start()
        datetime_format.return_value = "TIMESTAMP"

    def tearDown(self):
        super().tearDown()

    def test_get_profile_fields(self):
        with override_config(PROFILE_SECTIONS=self.PROFILE_SECTIONS):
            exporter = AttendeeExporter(self.site_event, self.owner)
            self.assertEqual(exporter.get_profile_fields(), [
                self.field_free,
                self.field_site_mandatory,
                self.field_group_mandatory
            ])
            self.assertEqual(exporter.column_headers(), [
                "Status", "Bijgewerkt", "Naam", "E-mail",
                "Free field", "Site mandatory field", "Group mandatory field"
            ])
            self.assertEqual(exporter.profile_common_values(self.site_attendee), [
                "Aanvaard",
                "TIMESTAMP",
                self.site_attendee.name,
                self.site_attendee.email,
            ])
            self.assertEqual([*exporter.profile_field_values(self.site_attendee)], [
                'Free field user1',
                'Site mandatory field user1',
                'Group mandatory field user1'
            ])

            exporter = AttendeeExporter(self.group_event, self.owner)
            self.assertEqual(exporter.get_profile_fields(), [
                self.field_free,
                self.field_group_mandatory
            ])
            self.assertEqual(exporter.column_headers(), [
                'Status', 'Bijgewerkt', 'Naam', 'E-mail',
                'Free field', 'Group mandatory field'
            ])
            self.assertEqual(exporter.profile_common_values(self.group_attendee), [
                'Aanvaard',
                'TIMESTAMP',
                self.group_attendee.name,
                self.group_attendee.email,
            ])
            self.assertEqual([*exporter.profile_field_values(self.group_attendee)], [
                'Free field user1',
                'Group mandatory field user1'
            ])
