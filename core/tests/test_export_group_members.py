from core.tests.helpers import PleioTenantTestCase
from core.models import Group
from mixer.backend.django import mixer
from user.factories import UserFactory
from core import config


class ExportGroupMembersTestCase(PleioTenantTestCase):

    def setUp(self):
        super(ExportGroupMembersTestCase, self).setUp()
        config.GROUP_MEMBER_EXPORT = True
        
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.group = mixer.blend(Group, owner = self.user1)
        self.group.join(self.user1)

    def test_export_group_members_not_logged_in(self):
        response = self.client.get("/exporting/group/{}".format(self.group.guid))
        self.assertEqual(response.status_code, 401)
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_export_group_members_not_admin(self):
        self.client.force_login(self.user2)
        response = self.client.get("/exporting/group/{}".format(self.group.guid))
        self.assertFalse(hasattr(response, 'streaming_content'))

    def test_export_group_members(self):
        self.client.force_login(self.user1)
        response = self.client.get("/exporting/group/{}".format(self.group.guid))
        self.assertIn('{};{};{}'.format(self.user1.guid,self.user1.name,self.user1.email), list(response.streaming_content)[1].decode())