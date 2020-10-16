from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group
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
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User, roles=['ADMIN'])
        self.group = mixer.blend(Group, owner=self.user1, is_closed=False, is_membership_on_request=False)
        self.group.join(self.user1, 'member')

        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            group=self.group
        )

    def tearDown(self):
        self.blog1.delete()
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()

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

        result = graphql_sync(schema, {"query": query, "variables": variables }, context_value={ "request": request })

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

        result = graphql_sync(schema, {"query": query, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

        # user2 is not in group and should not be able to read blog
        request.user = self.user2

        result = graphql_sync(schema, {"query": query, "variables": variables }, context_value={ "request": request })

        data = result[1]["data"]

        self.assertEqual(data["entity"], None)

        # user1 is in group and should be able to read blog
        request.user = self.user1

        result = graphql_sync(schema, {"query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]

        self.assertEqual(data["entity"]["accessId"], 4)

        # user3 is admin and should be able to read blog
        request.user = self.user3

        result = graphql_sync(schema, {"query": query, "variables": variables }, context_value={ "request": request })

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
                "description": "Public content possible?",
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
        request.user = self.user1

        result = graphql_sync(schema, { "query": mutation, "variables": data }, context_value={ "request": request })

        errors = result[1]["errors"]

        self.assertEqual(errors[0]["message"], "could_not_save")