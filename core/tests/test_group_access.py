from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group, GroupProfileFieldSetting, ProfileField, UserProfile, UserProfileField
from core.lib import access_id_to_acl
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from ariadne import graphql_sync
import json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer


class TestGroupAccess(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
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
        self.blog1.delete()
        self.site_user.delete()
        self.group_owner.delete()
        self.group_admin.delete()
        self.group_user.delete()
        self.group_user_blog_owner.delete()
        self.site_admin.delete()

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

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.blog1.guid
        }

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

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

        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.blog1.guid
        }

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

        # site_user is not in group and should not be able to read blog
        request.user = self.site_user

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

        # group_user is in group and should be able to read blog
        request.user = self.group_user

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["accessId"], 4)

        # site_admin is admin and should be able to read blog
        request.user = self.site_admin

        result = graphql_sync(schema, {"query": query, "variables": variables}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["accessId"], 4)

    def test_open_content_closed_group(self):
        self.group.is_closed = True
        self.group.save()

        data = {
            "input": {
                "guid": self.blog1.guid,
                "title": "Testing",
                "accessId": 2,
            }
        }
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

        request = HttpRequest()
        request.user = self.group_user_blog_owner

        result = graphql_sync(schema, {"query": mutation, "variables": data}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        # Public access not possible, it will be save with group accessId
        self.assertEqual(data["editEntity"]["entity"]["accessId"], 4)

    def test_group_owner_can_edit_content(self):
        self.group.is_closed = True
        self.group.save()

        data = {
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

        request = HttpRequest()
        request.user = self.group_owner

        result = graphql_sync(schema, {"query": mutation, "variables": data}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], "Update by admin")

    def test_group_admin_can_edit_content(self):
        self.group.is_closed = True
        self.group.save()

        data = {
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

        request = HttpRequest()
        request.user = self.group_admin

        result = graphql_sync(schema, {"query": mutation, "variables": data}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], "Update by admin")

    def test_site_admin_can_edit_content(self):
        self.group.is_closed = True
        self.group.save()

        data = {
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

        request = HttpRequest()
        request.user = self.site_admin

        result = graphql_sync(schema, {"query": mutation, "variables": data}, context_value={"request": request})

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["editEntity"]["entity"]["title"], "Update by admin")
