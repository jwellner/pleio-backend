import uuid
from http import HTTPStatus

from django.urls import reverse

from core.factories import GroupFactory
from core.models import Subgroup
from core.tests.helpers import PleioTenantTestCase, override_config
from user.factories import UserFactory


class ExportGroupMembersTestCase(PleioTenantTestCase):

    def setUp(self):
        super(ExportGroupMembersTestCase, self).setUp()

        self.group_admin = UserFactory()
        self.visitor = UserFactory()
        self.inactive_member = UserFactory(is_active=False)
        self.active_member = UserFactory()
        self.group = GroupFactory(owner=self.group_admin)
        self.group.join(self.inactive_member)
        self.group.join(self.active_member)

        self.subgroup = Subgroup.objects.create(name="Demo subgroup name",
                                                group=self.group)
        self.subgroup.members.add(self.inactive_member)
        self.subgroup.members.add(self.active_member)

    @override_config(IS_CLOSED=True)
    def test_export_group_members_not_logged_in(self):

        response = self.client.get(reverse("group_members_export", args=[self.group.guid]))
        content = response.getvalue().decode()

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertNotIn(self.group_admin.email, content)
        self.assertTemplateUsed("react.html")

    @override_config(GROUP_MEMBER_EXPORT=False)
    def test_export_group_members_not_enabled(self):
        self.client.force_login(self.group_admin)

        response = self.client.get(reverse("group_members_export", args=[self.group.guid]))

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed("react.html")

    @override_config(GROUP_MEMBER_EXPORT=True)
    def test_export_group_members_not_admin(self):
        self.client.force_login(self.visitor)
        response = self.client.get(reverse("group_members_export", args=[self.group.guid]))
        content = response.getvalue().decode()

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertNotIn(self.group_admin.email, content)
        self.assertTemplateUsed("react.html")

    @override_config(GROUP_MEMBER_EXPORT=True)
    def test_export_group_members(self):
        self.client.force_login(self.group_admin)
        response = self.client.get(reverse("group_members_export", args=[self.group.guid]))
        content = response.getvalue().decode()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.group_admin.email, content)
        self.assertIn(self.active_member.email, content)
        self.assertNotIn(self.inactive_member.email, content)
        self.assertIn(self.subgroup.name, content)

    @override_config(GROUP_MEMBER_EXPORT=True)
    def test_export_group_not_exists(self):
        no_group_guid = str(uuid.uuid4())
        self.client.force_login(self.group_admin)

        response = self.client.get(reverse("group_members_export", args=[no_group_guid]))

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed("react.html")
