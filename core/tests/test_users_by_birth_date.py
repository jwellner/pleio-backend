from core.models import ProfileField, UserProfileField
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import USER_ROLES
from mixer.backend.django import mixer
from django.utils import timezone
from datetime import timedelta
from core.lib import access_id_to_acl


class UsersByBirthDateTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User, name="Tt")
        self.user2 = mixer.blend(User, name="Specific_user_name_1")
        self.user3 = mixer.blend(User, name="User3")
        self.user4 = mixer.blend(User, name='Xx')
        self.user5 = mixer.blend(User, name="Public birthday")
        self.user6 = mixer.blend(User, name="Private birthday")
        self.admin1 = mixer.blend(User, roles=[USER_ROLES.ADMIN], name='Yy')

        self.birthday_field = ProfileField.objects.create(key='birthday', name='birthday', field_type='date_field')

        today = timezone.now()
        tomorrow = today + timedelta(days=1)
        overtomorrow = today + timedelta(days=2)
        next_months = today + timedelta(weeks=5)

        user1_bd = mixer.blend(UserProfileField, user_profile=self.user1.profile, profile_field=self.birthday_field, value=tomorrow.strftime("%Y-%m-%d"), read_access=access_id_to_acl(self.user1, 1))
        user3_bd = mixer.blend(UserProfileField, user_profile=self.user3.profile, profile_field=self.birthday_field, value=today.strftime("%Y-%m-%d"), read_access=access_id_to_acl(self.user3, 1))
        user4_bd = mixer.blend(UserProfileField, user_profile=self.user4.profile, profile_field=self.birthday_field, value=next_months.strftime("%Y-%m-%d"), read_access=access_id_to_acl(self.user4, 1))
        user5_bd = mixer.blend(UserProfileField, user_profile=self.user5.profile, profile_field=self.birthday_field, value=overtomorrow.strftime("%Y-%m-%d"), read_access=access_id_to_acl(self.user5, 2))
        user6_bd = mixer.blend(UserProfileField, user_profile=self.user6.profile, profile_field=self.birthday_field, value=overtomorrow.strftime("%Y-%m-%d"), read_access=access_id_to_acl(self.user6, 0))

        self.query = """
            query usersByBirthDate(
                $profileFieldGuid: String!
                $futureDays: Int
                $offset: Int
                $limit: Int
            )  {
            usersByBirthDate(profileFieldGuid: $profileFieldGuid, futureDays: $futureDays, offset: $offset, limit: $limit) {
                edges {
                    guid
                    email
                    name
                }
                total
            }
        }

        """

    def tearDown(self):
        super().tearDown()

    def test_users_by_birth_date_by_user(self):
        variables = {
            "profileFieldGuid": str(self.birthday_field.guid)
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["usersByBirthDate"]["total"], 3)
        self.assertEqual(data["usersByBirthDate"]["edges"][0]["name"], self.user3.name)
        self.assertEqual(len(data["usersByBirthDate"]["edges"]), 3)

    def test_users_by_birth_date_by_user_future(self):
        variables = {
            "profileFieldGuid": str(self.birthday_field.guid),
            "futureDays": 60
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["usersByBirthDate"]["total"], 4)
        self.assertEqual(data["usersByBirthDate"]["edges"][0]["name"], self.user3.name)
        self.assertEqual(len(data["usersByBirthDate"]["edges"]), 4)

    def test_users_by_birth_date_by_anonymous(self):
        variables = {
            "profileFieldGuid": str(self.birthday_field.guid)
        }

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]

        self.assertEqual(data["usersByBirthDate"]["total"], 1)
        self.assertEqual(data["usersByBirthDate"]["edges"][0]["name"], self.user5.name)
        self.assertEqual(len(data["usersByBirthDate"]["edges"]), 1)

    def test_users_by_birth_date_by_admin(self):
        variables = {
            "profileFieldGuid": str(self.birthday_field.guid),
            "futureDays": 60
        }

        self.graphql_client.force_login(self.admin1)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["usersByBirthDate"]["total"], 5)
        self.assertEqual(data["usersByBirthDate"]["edges"][0]["name"], self.user3.name)
        self.assertEqual(len(data["usersByBirthDate"]["edges"]), 5)
