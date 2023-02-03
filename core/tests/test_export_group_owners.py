import uuid

from django.urls import reverse
from mixer.backend.django import mixer

from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory, UserFactory


class ExportGroupOwnersTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory()
        self.admin = AdminFactory()
        self.group1 = mixer.blend(Group, owner=self.user1)

    def test_export_group_owners_not_logged_in(self):
        self.override_config(IS_CLOSED=False)
        response = self.client.get(reverse("group_owners_export"))
        content = response.getvalue().decode()

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(self.user1.email, content)
        self.assertTemplateUsed("react.html")

    def test_export_group_owners_not_admin(self):
        self.client.force_login(self.user1)

        response = self.client.get(reverse("group_owners_export"))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed("react.html")

    def test_export_group_owners(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("group_owners_export"))
        content = response.getvalue().decode()

        self.assertIn('{};{};{};0\r\n'.format(self.user1.name, self.user1.email, self.group1.name), content)

