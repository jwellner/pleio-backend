from unittest import mock

from mixer.backend.django import mixer
from django.utils import timezone

from blog.factories import BlogFactory
from core.constances import ENTITY_STATUS
from core.models import Revision
from core.tests.helpers import PleioTenantTestCase
from event.factories import EventFactory
from user.factories import UserFactory
from core.tasks.cronjobs import make_publication_revisions, _maybe_create_publication_revision


class TestRevisionCronjobTestCase(PleioTenantTestCase):

    def setUp(self):
        super(TestRevisionCronjobTestCase, self).setUp()

        self.recently = timezone.now() - timezone.timedelta(minutes=30)
        self.yesterday = timezone.now() - timezone.timedelta(days=1)

        self.user1 = UserFactory(email="user1@example.com")
        self.blog = BlogFactory(owner=self.user1,
                                title="Only valid blog post",
                                published=self.recently)
        self.event = EventFactory(owner=self.user1,
                                  title="Event, no revision support (last time I checked)",
                                  published=self.recently)
        self.blog2 = BlogFactory(owner=self.user1,
                                 title="Out of scope blog post",
                                 published=self.yesterday)

        self.revision = mixer.blend(Revision,
                                    _container=self.blog,
                                    content={"richDescription": "Content1", "statusPublished": ENTITY_STATUS.DRAFT},
                                    description="Version 1")

    def tearDown(self):
        self.blog2.delete()
        self.event.delete()
        self.blog.delete()
        self.user1.delete()

        super().tearDown()

    def test_revision_cronjob(self):
        # given
        previous_last_revision = self.blog.last_revision()

        # when
        _maybe_create_publication_revision(self.blog)

        # then
        last_revision = self.blog.last_revision()
        self.assertNotEqual(previous_last_revision, last_revision)
        self.assertTrue(last_revision.content == {"statusPublished": "published"})

    @mock.patch("core.tasks.cronjobs._maybe_create_publication_revision")
    def test_not_trying_non_revision_mixin_entities(self, maybe_create_publication_revision):
        make_publication_revisions(self.tenant.schema_name)

        self.assertEqual(maybe_create_publication_revision.call_count, 1)
        self.assertEqual(maybe_create_publication_revision.call_args.args[0], self.blog)
