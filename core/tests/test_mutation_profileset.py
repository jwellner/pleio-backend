from mixer.backend.django import mixer

from core.models import ProfileSet, ProfileField
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestMutationAddProfilesetManagerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.user = UserFactory()
        self.another_user = UserFactory()
        self.field = mixer.blend(ProfileField)
        self.profile_set = ProfileSet.objects.create(
            name="Test profile set",
            field=self.field,
        )

        self.query = '''
        mutation AddProfilesetManager($user: String!, $set: String!) {
            m: addProfileSetManager(userGuid: $user, profileSetGuid: $set) {
                user {
                    profileSetManager {
                        name
                    }
                }
                profileSet {
                    name
                }
            }
        }
        '''

        self.variables = {
            'set': self.profile_set.guid,
            'user': self.user.guid
        }

    def tearDown(self):
        self.admin.delete()
        self.user.delete()
        self.another_user.delete()
        self.field.delete()
        self.profile_set.delete()
        super().tearDown()

    def test_anonymous_assign_profileset_to_user(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.query, self.variables)

    def test_user_assign_profileset_to_user(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.another_user)
            self.graphql_client.post(self.query, self.variables)

    def test_assign_profileset_to_user(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, self.variables)

        self.assertEqual(self.profile_set.name, result['data']['m']['user']['profileSetManager'][0]['name'])
        self.assertEqual(self.profile_set.name, result['data']['m']['profileSet']['name'])


class TestMutationRemoveProfilesetManagerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.user = UserFactory()
        self.another_user = UserFactory()
        self.field = mixer.blend(ProfileField)
        self.profile_set = ProfileSet.objects.create(
            name="Test profile set",
            field=self.field,
        )
        self.profile_set.users.add(self.user)

        self.query = '''
        mutation RemoveProfilesetManager($user: String!, $set: String!) {
            m: removeProfileSetManager(userGuid: $user, profileSetGuid: $set) {
                user {
                    profileSetManager {
                        name
                    }
                }
                profileSet {
                    name
                }
            }
        }
        '''

        self.variables = {
            'set': self.profile_set.guid,
            'user': self.user.guid,
        }

    def tearDown(self):
        self.admin.delete()
        self.user.delete()
        self.another_user.delete()
        self.field.delete()
        self.profile_set.delete()
        super().tearDown()

    def test_anonymous_remove_profileset_to_user(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.query, self.variables)

    def test_user_remove_profileset_to_user(self):
        with self.assertGraphQlError("user_not_site_admin"):
            self.graphql_client.force_login(self.another_user)
            self.graphql_client.post(self.query, self.variables)

    def test_assign_profileset_to_user(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, self.variables)

        self.assertEqual([], result['data']['m']['user']['profileSetManager'])
        self.assertEqual(self.profile_set.name, result['data']['m']['profileSet']['name'])
