from mixer.backend.django import mixer
from django.utils import timezone

from blog.factories import BlogFactory
from core.constances import ENTITY_STATUS
from core.models import Revision
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from core.tasks.cronjobs import make_publication_revisions

class TestRevisionCronjobTestCase(PleioTenantTestCase):

    def setUp(self):
        super(TestRevisionCronjobTestCase, self).setUp()

        self.user1 = UserFactory()

        self.now = timezone.now()
        self.past = timezone.now() - timezone.timedelta(minutes=30)
        
        self.blog = BlogFactory(owner=self.user1, 
                                published=self.past)

        self.revision = mixer.blend(Revision,
            _container=self.blog,
            content={"richDescription": "Content1", "statusPublished": ENTITY_STATUS.DRAFT},
            description="Version 1"
        )

    def test_revision_cronjob(self):

        make_publication_revisions(self.tenant.schema_name)
        revision = self.blog.last_revision()

        self.assertTrue(revision.content == {"statusPublished": "published"})
