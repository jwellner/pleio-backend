from unittest import mock

from django.utils.timezone import localtime, timedelta

from core.models import AvatarExport
from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory, EditorFactory, UserFactory


class TestAvatarExportMutationTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.admin = AdminFactory()
        self.editor = EditorFactory()
        self.user = UserFactory()

        self.mutation = """
        mutation AvatarExports {
            exportAvatars {
                status
            }
        }
        """

    def test_anonymous_user(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.mutation, {})

    def test_unauthorized_users(self):
        for user, msg in ((self.user, 'authenticated user'),
                          (self.editor, 'editor')):
            with self.assertGraphQlError("user_not_site_admin", msg="unexpectedly did not find the correct error message for user %s" % msg):
                self.graphql_client.force_login(user)
                self.graphql_client.post(self.mutation, {})

    @mock.patch('core.tasks.exports.export_avatars.delay')
    def test_schedule_export_avatars(self, mocked_schedule_export):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, {})

        self.assertEqual(result['data']['exportAvatars']['status'], 'pending')
        self.assertTrue(mocked_schedule_export.called)

    @mock.patch('core.tasks.exports.export_avatars.delay')
    def test_schedule_export_avatars_when_former_is_ready(self, mocked_schedule_export):
        AvatarExport.objects.create(
            initiator=self.admin,
            status='ready'
        )
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, {})

        self.assertEqual(result['data']['exportAvatars']['status'], 'pending')
        self.assertTrue(mocked_schedule_export.called)

    @mock.patch('core.tasks.exports.export_avatars.delay')
    def test_prevent_duplicate_exports(self, mocked_schedule_export):
        AvatarExport.objects.create(
            initiator=self.admin,
            status='in_progress'
        )

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, {})

        self.assertFalse(mocked_schedule_export.called)
        self.assertEqual(result['data']['exportAvatars']['status'], 'in_progress')
        self.assertEqual(1, AvatarExport.objects.filter(initiator=self.admin).count())

    @mock.patch('core.tasks.exports.export_avatars.delay')
    def test_prevent_duplicate_exports(self, mocked_schedule_export):
        AvatarExport.objects.create(
            initiator=self.admin,
            status='in_progress',
            created_at=localtime() - timedelta(minutes=61)
        )

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, {})

        self.assertTrue(mocked_schedule_export.called)
        self.assertEqual(result['data']['exportAvatars']['status'], 'pending')
        self.assertEqual(2, AvatarExport.objects.filter(initiator=self.admin).count())
