from mixer.backend.django import mixer
from django.utils import timezone

from blog.models import Blog
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class ToggleEntityArchivedTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user = UserFactory()
        self.admin = UserFactory(roles=['ADMIN'])
        self.blog = mixer.blend(Blog)

        self.mutation = """
            mutation toggleEntityArchived($guid: String!) {
                toggleEntityArchived(guid: $guid) {
                    success
                }
            }
        """
        self.variables = {
            "guid": self.blog.guid
        }

    def test_toggle_entity_archived_anonymous_user(self):
        with self.assertGraphQlError('not_logged_in'):
            self.graphql_client.reset()
            self.graphql_client.post(self.mutation, self.variables)

    def test_toggle_entity_archived_by_user(self):
        with self.assertGraphQlError('could_not_save'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, self.variables)

    def test_toggle_entity_archived_by_admin(self):
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, self.variables)
        revision = self.blog.last_revision()

        self.assertTrue(result["data"]["toggleEntityArchived"]["success"])
        self.assertEqual([*revision.content.keys()], ['statusPublished', 'scheduleArchiveEntity'])
        self.assertEqual(revision.content['statusPublished'], "archived")

    def test_toggle_entity_published_by_admin(self):
        self.blog.is_archived = True
        self.blog.schedule_archive_after = timezone.now()
        self.blog.save()

        self.graphql_client.force_login(self.admin)
        self.graphql_client.post(self.mutation, self.variables)
        revision = self.blog.last_revision()

        self.assertEqual([*revision.content.keys()], ['statusPublished', 'scheduleArchiveEntity'])
        self.assertEqual(revision.content['statusPublished'], "published")

    def test_toggle_entity_archived_could_not_find(self):
        variables = {
            "guid": "43ee295a-5950-4330-8f0e-372f9f4caddf"
        }

        with self.assertGraphQlError('could_not_find'):
            self.graphql_client.force_login(self.user)
            self.graphql_client.post(self.mutation, variables)
