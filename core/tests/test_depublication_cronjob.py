from django.utils import timezone
from mixer.auto import mixer

from blog.models import Blog
from core.tasks.cronjobs import depublicate_content
from core.tests.helpers import PleioTenantTestCase
from user.models import User


class TestDepublicationCronjobTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = mixer.blend(User, name="owner", email="owner@example.com")

        self.now = timezone.localtime()
        self.future = timezone.localtime() + timezone.timedelta(days=1)

    def test_archive_entity(self):
        entity = mixer.blend(Blog, owner=self.owner,
                             is_archived=False,
                             schedule_archive_after=self.now)

        depublicate_content(self.tenant.schema_name)
        entity.refresh_from_db()

        self.assertTrue(entity.is_archived)

    def test_future_archive_entity(self):
        entity = mixer.blend(Blog, owner=self.owner,
                             is_archived=False,
                             schedule_archive_after=self.future)

        depublicate_content(self.tenant.schema_name)
        entity.refresh_from_db()

        self.assertFalse(entity.is_archived)

    def test_delete_entity(self):
        entity = mixer.blend(Blog, owner=self.owner,
                             schedule_delete_after=self.now)

        depublicate_content(self.tenant.schema_name)

        with self.assertRaises(Blog.DoesNotExist):
            entity.refresh_from_db()

    def test_future_delete_entity(self):
        entity = mixer.blend(Blog, owner=self.owner,
                             schedule_delete_after=self.future)

        depublicate_content(self.tenant.schema_name)

        self.assertTrue(Blog.objects.filter(id=entity.id).exists())
