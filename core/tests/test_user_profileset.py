from mixer.backend.django import mixer

from core.models import ProfileField, ProfileSet
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory


class TestUserProfilesetTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory(name="User")

        self.field = mixer.blend(ProfileField)
        self.profile_set = ProfileSet.objects.create(
            name="Test profile set",
            field=self.field,
        )
        self.profile_set.users.add(self.user)

        self.query = """
            query QueryViewer {
                viewer {
                    user {
                        guid
                        profileSetManager {
                            name
                            field {
                                guid
                            }
                        }
                    }
                    profileSetManager {
                        name
                        field {
                            guid
                        }
                    }
                }
            }
        """

    def tearDown(self):
        super().tearDown()

    def test_query_users(self):
        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, {})
        viewer = result['data']['viewer']
        user = viewer['user']
        self.assertEqual(user['profileSetManager'][0]['name'], self.profile_set.name)
        self.assertEqual(user['profileSetManager'][0]['field']['guid'], self.field.guid)
        self.assertEqual(viewer['profileSetManager'][0]['name'], self.profile_set.name)
        self.assertEqual(viewer['profileSetManager'][0]['field']['guid'], self.field.guid)


class TestGlobalProfilesetTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()

        self.field = mixer.blend(ProfileField)
        self.profile_set = ProfileSet.objects.create(
            name="Test profile set",
            field=self.field,
        )

        self.query = """
            query SiteSettings {
                siteSettings {
                    profileSets {
                        name
                        field {
                            guid
                        }
                    }
                }
            }
        """

    def tearDown(self):
        super().tearDown()

    def test_site_settings(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, {})
        profile_sets = result['data']['siteSettings']['profileSets']
        self.assertEqual(1, len(profile_sets))
        self.assertEqual(profile_sets[0]['name'], self.profile_set.name)
        self.assertEqual(profile_sets[0]['field']['guid'], self.profile_set.field.guid)
