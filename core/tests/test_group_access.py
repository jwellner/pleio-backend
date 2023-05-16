from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class TestGroupAccess(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.site_user = mixer.blend(User)
        self.group_owner = mixer.blend(User)
        self.group_admin = mixer.blend(User)
        self.group_user_blog_owner = mixer.blend(User)
        self.group_user = mixer.blend(User)
        self.site_admin = mixer.blend(User, roles=['ADMIN'])
        self.group = mixer.blend(Group, owner=self.group_owner, is_closed=False, is_membership_on_request=False)
        self.group.join(self.group_owner, 'owner')
        self.group.join(self.group_admin, 'admin')
        self.group.join(self.group_user_blog_owner, 'member')
        self.group.join(self.group_user, 'member')

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.group_user_blog_owner,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.group_user_blog_owner.id)],
            group=self.group
        )

    def tearDown(self):
        super().tearDown()

    def test_open_group(self):
        query = """
            query BlogItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    ...BlogDetailFragment
                    __typename
                }
            }
            fragment BlogDetailFragment on Blog {
                title
                accessId
            }
        """

        variables = {
            "guid": self.blog1.guid
        }

        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["accessId"], 2)

    def test_closed_group(self):
        self.group.is_closed = True
        self.group.save()

        query = """
            query BlogItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    ...BlogDetailFragment
                    __typename
                }
            }
            fragment BlogDetailFragment on Blog {
                title
                accessId
            }
        """

        variables = {
            "guid": self.blog1.guid
        }

        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"], None)

        # site_user is not in group and should not be able to read blog
        self.graphql_client.force_login(self.site_user)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"], None)

        # group_user is in group and should be able to read blog
        self.graphql_client.force_login(self.group_user)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["accessId"], 4)

        # site_admin is admin and should be able to read blog
        self.graphql_client.force_login(self.site_admin)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["accessId"], 4)

    def test_open_content_closed_group(self):
        self.group.is_closed = True
        self.group.save()

        mutation = """
            fragment BlogParts on Blog {
                accessId
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        guid
                        status
                        ...BlogParts
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "title": "Testing",
                "accessId": 2,
            }
        }

        self.graphql_client.force_login(self.group_user_blog_owner)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        # Public access not possible, it will be save with group accessId
        self.assertEqual(data["editEntity"]["entity"]["accessId"], 4)

    def test_group_owner_can_edit_content(self):
        self.group.is_closed = True
        self.group.save()

        mutation = """
            fragment BlogParts on Blog {
                title
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        guid
                        status
                        ...BlogParts
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "title": "Update by admin",
            }
        }

        self.graphql_client.force_login(self.group_owner)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editEntity"]["entity"]["title"], "Update by admin")

    def test_group_admin_can_edit_content(self):
        self.group.is_closed = True
        self.group.save()

        mutation = """
            fragment BlogParts on Blog {
                title
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        guid
                        status
                        ...BlogParts
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog1.guid,
                "title": "Update by admin",
            }
        }

        self.graphql_client.force_login(self.group_admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editEntity"]["entity"]["title"], "Update by admin")

    def test_site_admin_can_edit_content(self):
        self.group.is_closed = True
        self.group.save()

        variables = {
            "input": {
                "guid": self.blog1.guid,
                "title": "Update by admin",
            }
        }
        mutation = """
            fragment BlogParts on Blog {
                title
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                        guid
                        status
                        ...BlogParts
                    }
                }
            }
        """

        self.graphql_client.force_login(self.site_admin)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editEntity"]["entity"]["title"], "Update by admin")
