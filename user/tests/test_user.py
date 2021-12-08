from core.lib import access_id_to_acl
from core.models import ProfileField, UserProfileField
from datetime import datetime
from django.contrib.auth.models import AnonymousUser
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from user.models import User

class UserTestCase(FastTenantTestCase):
    def setUp(self):
        self.birthday_field = ProfileField.objects.create(key='birthday', name='birthday', field_type='date_field')
        self.user = AnonymousUser()

    def create_user_with_bday(self, date):
        user = mixer.blend(User, email=date)

        bd = mixer.blend(
            UserProfileField,
            user_profile=user.profile,
            profile_field=self.birthday_field,
            value=date,
            read_access=access_id_to_acl(user, 2))

        return user

    def test_users_by_birthday_sorted(self):
        first = self.create_user_with_bday("2021-12-02")
        second = self.create_user_with_bday("2021-12-03")
        third = self.create_user_with_bday("2021-12-04")
        start_date = datetime.strptime("2021-12-01", "%Y-%m-%d")
        end_date = datetime.strptime("2021-12-05", "%Y-%m-%d")

        users = User.objects.get_upcoming_birthday_users(self.birthday_field.guid, self.user, start_date, end_date).edges

        self.assertListEqual([first, second, third], users)

    def test_users_by_birthday_excluding_later_bdays(self):
        first = self.create_user_with_bday("2021-12-02")
        second = self.create_user_with_bday("2021-12-03")
        too_late = self.create_user_with_bday("2021-12-06")
        start_date = datetime.strptime("2021-12-01", "%Y-%m-%d")
        end_date = datetime.strptime("2021-12-05", "%Y-%m-%d")

        users = User.objects.get_upcoming_birthday_users(self.birthday_field.guid, self.user, start_date, end_date).edges

        self.assertListEqual([first, second], users)

    def test_users_by_birthday_sorted_across_years(self):
        second = self.create_user_with_bday("1975-01-05")
        first = self.create_user_with_bday("2000-12-31")
        start_date = datetime.strptime("2021-12-01", "%Y-%m-%d")
        end_date = datetime.strptime("2022-01-31", "%Y-%m-%d")

        users = User.objects.get_upcoming_birthday_users(self.birthday_field.guid, self.user, start_date, end_date).edges

        self.assertListEqual([first, second], users)

    def test_users_by_birthday_reality(self):
        self.create_user_with_bday("1980-12-13"),
        self.create_user_with_bday("1982-12-24"),
        self.create_user_with_bday("1992-12-27"),
        self.create_user_with_bday("1971-12-28"),

        expected_users = [
            self.create_user_with_bday("1980-12-04"),
            self.create_user_with_bday("1974-12-09"),
            self.create_user_with_bday("1990-12-11"),
            self.create_user_with_bday("1900-12-11"),
            self.create_user_with_bday("1991-12-12"),
        ]

        # extra's outside of limit
        self.create_user_with_bday("1978-12-12"),
        self.create_user_with_bday("1993-12-30"),
        self.create_user_with_bday("1975-01-01"),
        self.create_user_with_bday("1955-01-05"),

        start_date = datetime.strptime("2021-12-04", "%Y-%m-%d")
        end_date = datetime.strptime("2022-01-06", "%Y-%m-%d")

        users = User.objects.get_upcoming_birthday_users(self.birthday_field.guid, self.user, start_date, end_date, 0,  5).edges

        self.assertListEqual(expected_users, users)
