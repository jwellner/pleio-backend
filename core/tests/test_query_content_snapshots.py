from unittest import mock

from django.core.files.base import ContentFile

from core.tests.helpers import PleioTenantTestCase
from core.utils.export.content import ContentSnapshot
from file.factories import FileFactory
from user.factories import UserFactory


class TestContentSnapshotsTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.authenticated_user = UserFactory()
        self.other_user = UserFactory()

        self.my_content_summary = FileFactory(owner=self.authenticated_user,
                                              title="my content summary",
                                              tags=[ContentSnapshot.EXCLUDE_TAG],
                                              upload=ContentFile(b"Content summary", 'activities.zip'))
        self.not_content_summary = FileFactory(owner=self.authenticated_user,
                                               title="not my content summary",
                                               upload=ContentFile(b"Not summary", 'not-summary.zip'))
        self.others_content_summary = FileFactory(owner=self.other_user,
                                                  title="otherones content summary",
                                                  tags=[ContentSnapshot.EXCLUDE_TAG],
                                                  upload=ContentFile(b'Others content summary', 'activities.zip'))

        self.query = """
        query ContentSnapshots {
            contentSnapshots {
                edges {
                    ... on File {
                        guid
                        title
                        tags
                    }
                }
            }
        }
        """

    def tearDown(self):
        super().tearDown()

    def test_anonymous_user_has_no_access(self):
        with self.assertGraphQlError("not_logged_in"):
            self.graphql_client.post(self.query, {})

    def test_authenticated_user_sees_own_content_only(self):
        self.graphql_client.force_login(self.authenticated_user)
        response = self.graphql_client.post(self.query, {})
        edges = response['data']['contentSnapshots']['edges']

        self.assertEqual(1, len(edges))
        self.assertEqual(self.my_content_summary.guid, edges[0]['guid'])


class TestCreateContentSnapshotTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.query = """
        mutation ContentSnapshots {
            createContentSnapshot {
                success
                edges {
                    ... on File {
                        guid
                    }
                }
            }
        }
        """

    def tearDown(self):
        super().tearDown()

    def test_anonymous_users_have_no_access(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.post(self.query, {})

    @mock.patch("core.tasks.exports.export_my_content")
    def test_create_content_snapshot(self, mocked_export_my_content):
        self.graphql_client.force_login(self.user)
        response = self.graphql_client.post(self.query, {})

        self.assertEqual(1, mocked_export_my_content.delay.call_count)
        self.assertEqual(True, response['data']['createContentSnapshot']['success'])
        self.assertEqual(0, len(response['data']['createContentSnapshot']['edges']))