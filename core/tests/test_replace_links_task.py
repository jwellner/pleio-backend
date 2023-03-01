from unittest import mock

from blog.factories import BlogFactory
from core.factories import GroupFactory
from core.models import Comment
from core.tasks import replace_domain_links
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestReplaceLinksTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.previous_domain = 'legacy-domain-name'

        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner)
        self.blog = BlogFactory(owner=self.owner, group=self.group)
        self.blog2 = BlogFactory(owner=self.owner, group=self.group)
        self.comment = Comment.objects.create(
            container=self.blog,
            owner=self.owner
        )

    def populate_rich_fields(self, content):
        self.group.rich_description = content
        self.group.save()

        self.blog.rich_description = content
        self.blog.save()

        self.comment.rich_description = content
        self.comment.save()

    def test_replace_links(self):
        # Given
        self.populate_rich_fields(f"https://{self.previous_domain}/some-location")

        # When
        replace_domain_links(self.tenant.schema_name, self.previous_domain)
        self.group.refresh_from_db()
        self.blog.refresh_from_db()
        self.comment.refresh_from_db()

        self.assertNotIn(self.previous_domain, self.group.rich_description)
        self.assertNotIn(self.previous_domain, self.blog.rich_description)
        self.assertNotIn(self.previous_domain, self.comment.rich_description)

    def test_replace_links_calls_save(self):
        # Given
        self.populate_rich_fields(f"https://{self.previous_domain}/some-location")
        save_group = mock.patch("core.models.group.Group.save").start()
        save_blog = mock.patch("blog.models.Blog.save").start()
        save_comment = mock.patch("core.models.comment.Comment.save").start()

        # When
        replace_domain_links(self.tenant.schema_name, self.previous_domain)

        # Then
        self.assertEqual(save_blog.call_count, 1)
        self.assertEqual(save_group.call_count, 1)
        self.assertEqual(save_comment.call_count, 1)

    def test_replace_links_nothing_to_do(self):
        # Do all the same as test_replace_links
        self.populate_rich_fields("No links in content")

        save_group = mock.patch("core.models.group.Group.save").start()
        save_blog = mock.patch("blog.models.Blog.save").start()
        save_comment = mock.patch("core.models.comment.Comment.save").start()

        # When
        replace_domain_links(self.tenant.schema_name, self.previous_domain)

        # Then
        self.assertFalse(save_group.called)
        self.assertFalse(save_blog.called)
        self.assertFalse(save_comment.called)
