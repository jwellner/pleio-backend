from django.utils.timezone import localtime, timedelta
from django_tenants.test.cases import TenantTestCase

from blog.factories import BlogFactory
from core.tasks import catchup_with_last_action


class TestCatchupWithLastActionTestCase(TenantTestCase):
    def test_date_published(self):
        blog1 = BlogFactory(published=localtime() + timedelta(days=1),
                            last_action=localtime() - timedelta(days=1))
        blog2 = BlogFactory(published=localtime() - timedelta(days=1),
                            last_action=localtime() - timedelta(days=2))
        blog3 = BlogFactory(published=localtime() - timedelta(days=2),
                            last_action=localtime() - timedelta(days=1))

        catchup_with_last_action(self.tenant.schema_name)

        blog1.refresh_from_db()
        self.assertTrue(blog1.published > blog1.last_action)

        blog2.refresh_from_db()
        self.assertTrue(blog2.published == blog2.last_action)

        blog3.refresh_from_db()
        self.assertTrue(blog3.published < blog3.last_action)
