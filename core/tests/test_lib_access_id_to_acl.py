from blog.factories import BlogFactory
from core.constances import ACCESS_TYPE
from core.factories import GroupFactory
from core.lib import access_id_to_acl
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestLibGetAccessIdsClosedSiteTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner,
                                  name="Foo",
                                  is_closed=True)
        self.subgroup = self.group.subgroups.create(name='Foo')
        self.blog = BlogFactory(owner=self.owner,
                                group=self.group)

    def tearDown(self):
        self.group.delete()
        self.blog.delete()
        self.owner.delete()
        super().tearDown()

    def test_blog_access_id_to_acl(self):
        levels = [
            ('0', 'Private access', [ACCESS_TYPE.user.format(self.owner.guid)]),
            ('1', 'Logged in access', [ACCESS_TYPE.user.format(self.owner.guid),
                                     ACCESS_TYPE.group.format(self.group.guid)]),
            ('2', 'Public access', [ACCESS_TYPE.user.format(self.owner.guid),
                                  ACCESS_TYPE.group.format(self.group.guid)]),
            ('4', 'Group access', [ACCESS_TYPE.user.format(self.owner.guid),
                                 ACCESS_TYPE.group.format(self.group.guid)]),
            (self.subgroup.access_id, 'Subgroup access', [ACCESS_TYPE.user.format(self.owner.guid),
                                                          ACCESS_TYPE.subgroup.format(self.subgroup.access_id)]),
        ]
        for id, msg, expected_acl in levels:
            self.assertEqual(access_id_to_acl(self.blog, id), expected_acl, msg="Testing for %s" % msg)

    def test_blog_at_open_group_access_id_to_acl(self):
        self.group.is_closed = False
        self.group.save()

        levels = [
            ('0', 'Private access', [ACCESS_TYPE.user.format(self.owner.guid)]),
            ('1', 'Logged in access', [ACCESS_TYPE.user.format(self.owner.guid),
                                     ACCESS_TYPE.logged_in]),
            ('2', 'Public access', [ACCESS_TYPE.user.format(self.owner.guid),
                                  ACCESS_TYPE.public]),
            ('4', 'Group access', [ACCESS_TYPE.user.format(self.owner.guid),
                                 ACCESS_TYPE.group.format(self.group.guid)]),
            (self.subgroup.access_id, 'Subgroup access', [ACCESS_TYPE.user.format(self.owner.guid),
                                                          ACCESS_TYPE.subgroup.format(self.subgroup.access_id)]),
        ]
        for id, msg, expected_acl in levels:
            self.assertEqual(access_id_to_acl(self.blog, id), expected_acl, msg="Testing for %s" % msg)

    def test_non_group_blog_access_id_to_acl(self):
        self.blog.group = None
        self.blog.save()

        levels = [
            ('0', 'Private access', [ACCESS_TYPE.user.format(self.owner.guid)]),
            ('1', 'Logged in access', [ACCESS_TYPE.user.format(self.owner.guid),
                                     ACCESS_TYPE.logged_in]),
            ('2', 'Public access', [ACCESS_TYPE.user.format(self.owner.guid),
                                  ACCESS_TYPE.public]),
        ]
        for id, msg, expected_acl in levels:
            self.assertEqual(access_id_to_acl(self.blog, id), expected_acl, msg="Testing for %s" % msg)
