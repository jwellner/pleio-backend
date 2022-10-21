from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer

from blog.models import Blog
from core import override_local_config
from core.models import Group
from core.post_deploy import migrate_categories
from user.factories import UserFactory


class TestCategoryTagMigrationTestCase(FastTenantTestCase):
    CATEGORIES = [{"name": "Demo",
                   "values": ["One", "Two", "Three"]},
                  {"name": "Lition",
                   "values": ["First", "Second", "Third"]}]

    @override_local_config(TAG_CATEGORIES=CATEGORIES)
    def test_migrate_blog(self):
        blog = mixer.blend(Blog,
                           tags=["One"])
        migrate_categories()
        blog.refresh_from_db()

        self.assertEqual(blog.tags, [])
        self.assertEqual(blog.category_tags, [
            {"name": "Demo", "values": ["One"]}
        ])

    @override_local_config(TAG_CATEGORIES=CATEGORIES)
    def test_migrate_group(self):
        group = mixer.blend(Group,
                            tags=["Two", "First", "Extra"])
        migrate_categories()
        group.refresh_from_db()

        self.assertEqual(group.tags, ["Extra"])
        self.assertEqual(group.category_tags, [
            {"name": "Demo", "values": ["Two"]},
            {"name": "Lition", "values": ["First"]}
        ])

    @override_local_config(TAG_CATEGORIES=CATEGORIES)
    def test_migrate_user(self):
        user = UserFactory()
        profile = user.profile
        profile.overview_email_tags = ["Third", "Foo", "Baz"]
        profile.save()

        migrate_categories()
        profile.refresh_from_db()

        self.assertEqual(profile.overview_email_tags, ["Foo", "Baz"])
        self.assertEqual(profile.overview_email_categories, [
            {"name": "Lition", "values": ["Third"]}
        ])
