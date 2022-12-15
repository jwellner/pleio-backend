from mixer.backend.django import mixer

from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import AdminFactory, UserFactory


class ExportGroupOwnersTestCase(PleioTenantTestCase):

    def setUp(self):
        super(ExportGroupOwnersTestCase, self).setUp()
        
        self.user1 = UserFactory()
        self.admin = AdminFactory()
        self.group1 = mixer.blend(Group, owner = self.user1)

    def test_export_group_owners_not_logged_in(self):
        response = self.client.get("/exporting/group-owners")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_export_group_owners_not_admin(self):
        self.client.force_login(self.user1)
        response = self.client.get("/exporting/group-owners")
        self.assertTemplateUsed(response, 'react.html')
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_export_group_owners(self):
        self.client.force_login(self.admin)
        response = self.client.get("/exporting/group-owners")
        self.assertTemplateNotUsed(response, 'react.html')
        self.assertEqual(list(response.streaming_content)[1].decode(), 
            '{};{};{};0\r\n'.format(self.user1.name, self.user1.email, self.group1.name))
