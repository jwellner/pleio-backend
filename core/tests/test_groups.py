from django.core.files.base import ContentFile

from blog.factories import BlogFactory
from core.factories import GroupFactory, AttachmentFactory
from core.tests.helpers import PleioTenantTestCase
from core.models import Group
from file.factories import FileFactory
from user.factories import AdminFactory, UserFactory
from user.models import User
from mixer.backend.django import mixer


class GroupsEmptyTestCase(PleioTenantTestCase):

    def test_groups_empty(self):
        query = """
            {
                groups {
                    total
                    edges {
                        guid
                        name
                    }
                }
            }
        """

        result = self.graphql_client.post(query, {})

        data = result["data"]

        self.assertEqual(data["groups"]["total"], 0)
        self.assertEqual(data["groups"]["edges"], [])


class GroupsNotEmptyTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.group1 = mixer.blend(Group,
                                  name="Group 1")
        self.group1.join(self.user, 'member')
        self.groups = mixer.cycle(5).blend(Group, is_closed=False)
        self.group2 = mixer.blend(Group, is_featured=True,
                                  name="Group 2")
        self.query = """
            query GroupsQuery(
                    $filter: GroupFilter
                    $offset: Int
                    $limit: Int
                    $q: String) {
                groups(
                        filter: $filter
                        offset: $offset
                        limit: $limit
                        q: $q) {
                    total
                    edges {
                        guid
                        name
                    }
                }
            }
        """

    def tearDown(self):
        for group in self.groups:
            group.delete()
        self.group1.delete()
        self.group2.delete()
        self.user.delete()
        super().tearDown()

    def test_groups_default(self):
        result = self.graphql_client.post(self.query, {})

        data = result["data"]

        self.assertEqual(data["groups"]["total"], 7)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group2.guid)

    def test_groups_limit(self):
        result = self.graphql_client.post(self.query, {'limit': 1})

        data = result["data"]

        self.assertEqual(data["groups"]["total"], 7)

    def test_groups_mine(self):
        variables = {
            "filter": "mine",
            "offset": 0,
            "limit": 20,
            "q": ""
        }
        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]

        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group1.guid)


class HiddenGroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticated_user = mixer.blend(User, name="yy")
        self.group_member_user = mixer.blend(User, name="xx")
        self.non_member_user = mixer.blend(User, name="yyy")
        self.group = mixer.blend(Group, owner=self.authenticated_user,
                                 introduction='introductionMessage',
                                 is_hidden=True)
        self.group.join(self.group_member_user, 'member')
        self.admin = AdminFactory()

    def test_hidden_group_is_hidden_for_non_members(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
               }
            }
        """

        self.graphql_client.force_login(self.non_member_user)
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(data["groups"]["total"], 0)

    def test_hidden_group_is_visible_for_members(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
                    edges {      
                        guid
                    }    
               }
            }
        """

        self.graphql_client.force_login(self.group_member_user)
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group.guid)

    def test_hidden_group_is_hidden_for_anonymous_users(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
               }
            }
        """
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(data["groups"]["total"], 0)

    def test_hidden_group_is_visible_for_admin_users(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
                    edges {      
                        guid
                    }    
               }
            }
        """
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group.guid)


class TestGroupDiskSize(PleioTenantTestCase):
    ONE_CONTENT = '1'
    TWO_CONTENT = '22'
    THREE_CONTENT = '333'
    FIVE_CONTENT = '55555'
    SEVEN_CONTENT = '7777777'
    ELEVEN_CONTENT = '11111111111'

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.group1 = GroupFactory(owner=self.owner)
        self.blog1 = BlogFactory(owner=self.owner, group=self.group1)
        self.file1 = FileFactory(
            owner=self.owner,
            upload=ContentFile(self.ONE_CONTENT, "Test1.txt"),
            group=self.group1)
        self.file2 = FileFactory(
            owner=self.owner,
            upload=ContentFile(self.TWO_CONTENT, "Test2.txt"),
            group=self.group1)
        self.attachment3 = AttachmentFactory(
            attached=self.blog1,
            upload=ContentFile(self.THREE_CONTENT, "Test3.txt"))

        self.group2 = GroupFactory(owner=self.owner)
        self.file4 = FileFactory(
            owner=self.owner,
            upload=ContentFile(self.FIVE_CONTENT, "Test4.txt"),
            group=self.group2)
        self.file5 = FileFactory(
            owner=self.owner,
            upload=ContentFile(self.SEVEN_CONTENT, "Test5.txt"),
            group=self.group2)
        self.attachment6 = AttachmentFactory(
            attached=self.group2,
            upload=ContentFile(self.ELEVEN_CONTENT, "Test6.txt"))

        self.group3 = GroupFactory(owner=self.owner)

    def tearDown(self):
        self.attachment6.delete()
        self.file5.delete()
        self.file4.delete()
        self.group2.delete()

        self.attachment3.delete()
        self.file2.delete()
        self.file1.delete()
        self.group1.delete()

        self.group3.delete()

        self.owner.delete()
        super().tearDown()

    def test_disk_size(self):
        self.assertEqual(self.group1.disk_size(), 6)
        self.assertEqual(self.group2.disk_size(), 23)
        self.assertEqual(self.group3.disk_size(), 0)