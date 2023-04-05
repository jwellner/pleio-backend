import uuid

from django.utils.dateformat import format as dateformat

from core.constances import ACCESS_TYPE
from core.lib import datetime_isoformat
from core.models import ProfileField, UserProfileField
from core.tests.helpers import PleioTenantTestCase
from core.views import Echo
from user.exception import ExportError
from user.exporting import ExportUsers
from user.factories import UserFactory
from user.models import User


class TestExportUsers(PleioTenantTestCase):
    """ Test the user.exporting.ExportUsers member functions"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_get_native_field(self):
        exporter = ExportUsers(User.objects.none(),
                               user_fields=[n.field for n in ExportUsers.AVAILABLE_SERIALIZERS],
                               profile_field_guids=[])

        self.assertEqual([*exporter.get_native_fields(self.user)], [
            self.user.guid,
            self.user.name,
            self.user.email,
            datetime_isoformat(self.user.created_at),
            datetime_isoformat(self.user.updated_at),
            '', False, '', '', False,
            dateformat(self.user.created_at, 'U'),
            dateformat(self.user.updated_at, 'U'),
            ''
        ])
        # NOTE: It are fields as given in the url parameters; NOT LABELS!
        self.assertEqual(exporter.get_headers(), [n.field for n in ExportUsers.AVAILABLE_SERIALIZERS])

    def test_invalid_field_input(self):
        exporter = ExportUsers(User.objects.none(),
                               user_fields=['foo'],
                               profile_field_guids=[])
        self.assertEqual([*exporter.get_native_fields(self.user)], [])

    def test_invalid_profile_field_input(self):
        exporter = ExportUsers(User.objects.none(),
                               user_fields=[],
                               profile_field_guids=[uuid.uuid4()])
        try:
            self.assertEqual([*exporter.get_headers()], [])
            self.fail("Unexpectedly did not raise an exception.")  # pragma: no cover
        except ExportError as e:
            self.assertEqual(str(e), "Profile field can not be exported")

    def test_get_profile_fields(self):
        profile_field = ProfileField.objects.create(key='text_key', name='Foo baz', field_type='text_field')
        profile_value = UserProfileField.objects.create(user_profile=self.user.profile,
                                                        profile_field=profile_field,
                                                        value="Foo bar",
                                                        read_access=[ACCESS_TYPE.logged_in])
        exporter = ExportUsers(User.objects.none(),
                               user_fields=[],
                               profile_field_guids=[str(profile_field.pk)])

        self.assertEqual([*exporter.get_profile_fields(self.user)], ["Foo bar"])
        self.assertEqual(exporter.get_headers(), ["Foo baz"])

        # test user that hasn't filled in the profile field
        extra_user = UserFactory()
        self.assertEqual([*exporter.get_profile_fields(extra_user)], [""])


    def test_get_data_and_stream(self):
        profile_field = ProfileField.objects.create(key='text_key', name='Foo baz', field_type='text_field')
        profile_value = UserProfileField.objects.create(user_profile=self.user.profile,
                                                        profile_field=profile_field,
                                                        value="Foo bar",
                                                        read_access=[ACCESS_TYPE.logged_in])
        exporter = ExportUsers([self.user],
                               user_fields=['name', 'email'],
                               profile_field_guids=[str(profile_field.pk)])

        # Test get_data
        self.assertEqual([*exporter.get_data(self.user)], [
            self.user.name,
            self.user.email,
            "Foo bar"
        ])
        self.assertEqual(exporter.get_headers(), ["name", "email", "Foo baz"])

        # Test stream
        result = ''.join([*exporter.stream(Echo())])
        self.assertEqual(result,
                         "name;email;Foo baz\r\n" +
                         f"{self.user.name};{self.user.email};Foo bar\r\n")
