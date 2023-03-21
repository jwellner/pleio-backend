from django_tenants.utils import schema_context

from control.tasks import copy_group, add_site
from core.tests.helpers import PleioTenantTestCase, suppress_stdout
from core.models import Group, Entity
from core.factories import GroupFactory
from blog.factories import BlogFactory
from user.factories import UserFactory


class TestTaskCopyGroupTestCase(PleioTenantTestCase):

    @suppress_stdout()
    def setUp(self):
        super(TestTaskCopyGroupTestCase, self).setUp()

        with schema_context("public"):
            add_site('demo1', 'demo1.local')
            add_site('demo2', 'demo2.local')
            self.control_user = UserFactory()

        with schema_context("demo1"):
            self.user = UserFactory()
            self.group = GroupFactory(owner=self.user, name="Hello")
            self.content1 = BlogFactory(owner=self.user, group=self.group)
            self.content2 = BlogFactory(owner=self.user, group=self.group)

    @suppress_stdout()
    def test_copy_group_to_schema(self):
        with schema_context("public"):
            result = copy_group('demo1', self.control_user.guid, self.group.guid, 'demo2')
        
        with schema_context("demo2"):
            assert Group.objects.filter(name="Copy: %s" % self.group.name).exists(), "Copy should exist in tenant demo2"
            assert Entity.objects.filter(group__name="Copy: %s" % self.group.name).count() == 2, "Copy should have 2 entities"

    @suppress_stdout()
    def test_copy_group_self(self):
        with schema_context("public"):
            result = copy_group('demo1', self.control_user.guid, self.group.guid)
        
        with schema_context("demo1"):
            assert Group.objects.filter(name="Copy: %s" % self.group.name).exists(), "Copy should exist in tenant demo1"
            assert Entity.objects.filter(group__name="Copy: %s" % self.group.name).count() == 2, "Copy should have 2 entities"