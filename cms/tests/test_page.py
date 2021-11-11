from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from core.models import Group, GroupInvitation
from user.models import User
from file.models import FileFolder
from core.constances import ACCESS_TYPE
from backend2.schema import schema
from django.utils.text import slugify
from ariadne import graphql_sync
import json
from cms.models import Page
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from mixer.backend.django import mixer

class PageTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.page_parent = Page.objects.create(owner=self.user1,
                                               read_access=[ACCESS_TYPE.public],
                                               write_access=[ACCESS_TYPE.user.format(self.user1.id)],
                                               title="Test parent page",
                                               rich_description="JSON to string",
                                               )
        self.page_child = Page.objects.create(owner=self.user1,
                                              read_access=[ACCESS_TYPE.public],
                                              write_access=[ACCESS_TYPE.user.format(self.user1.id)],
                                              title="Test child page",
                                              rich_description="JSON to string",
                                              parent=self.page_parent
                                              )
        self.page_child2 = Page.objects.create(owner=self.user2,
                                              read_access=[ACCESS_TYPE.user.format(self.user2.id)],
                                              write_access=[ACCESS_TYPE.user.format(self.user2.id)],
                                              title="Test child page other user",
                                              rich_description="JSON to string",
                                              parent=self.page_parent
                                              )
        self.page_child_child = Page.objects.create(owner=self.user1,
                                                    read_access=[ACCESS_TYPE.public],
                                                    write_access=[ACCESS_TYPE.user.format(self.user1.id)],
                                                    title="Test child of child page",
                                                    rich_description="JSON to string",
                                                    parent=self.page_child
                                                    )

    def tearDown(self):
        self.page_parent.delete()
        self.user1.delete()

    def test_parent_page_by_anonymous(self):

        query = """
            query PageItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...PageDetailFragment
                    __typename
                }
            }

            fragment PageDetailFragment on Page {
                pageType
                canEdit
                title
                url
                richDescription
                tags
                accessId
                parent {
                    guid
                }
                hasChildren
                children {
                    guid
                    title
                    canEdit
                    children {
                        guid
                        title
                        canEdit
                        children {
                            guid
                            title
                        }
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.anonymousUser

        variables = {
            "guid": self.page_parent.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["entity"]["title"], "Test parent page")
        self.assertEqual(data["entity"]["richDescription"], "JSON to string")
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["parent"], None)
        self.assertEqual(data["entity"]["hasChildren"], True)
        self.assertEqual(data["entity"]["url"], "/cms/view/{}/{}".format(self.page_parent.guid, slugify(self.page_parent.title)))
        self.assertEqual(len(data["entity"]["children"]), 1)
        self.assertEqual(data["entity"]["children"][0]["guid"], self.page_child.guid)
        self.assertEqual(data["entity"]["children"][0]["children"][0]["guid"], self.page_child_child.guid)



    def test_child_page_by_owner(self):

        query = """
            query PageItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...PageDetailFragment
                    __typename
                }
            }

            fragment PageDetailFragment on Page {
                pageType
                canEdit
                title
                url
                richDescription
                tags
                accessId
                parent {
                    guid
                }
                hasChildren
                children {
                    guid
                    title
                    canEdit
                    children {
                        guid
                        title
                        canEdit
                        children {
                            guid
                            title
                        }
                    }
                }
            }
        """
        request = HttpRequest()
        request.user = self.user1

        variables = {
            "guid": self.page_child.guid
        }

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ "request": request })

        self.assertTrue(result[0])

        data = result[1]["data"]
        self.assertEqual(data["entity"]["title"], "Test child page")
        self.assertEqual(data["entity"]["richDescription"], "JSON to string")
        self.assertEqual(data["entity"]["tags"], [])
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["canEdit"], False)
        self.assertEqual(data["entity"]["parent"]["guid"], self.page_parent.guid)
        self.assertEqual(data["entity"]["hasChildren"], True)
        self.assertEqual(data["entity"]["url"], "/cms/view/{}/{}".format(self.page_child.guid, slugify(self.page_child.title)))
        self.assertEqual(data["entity"]["children"][0]["guid"], self.page_child_child.guid)
