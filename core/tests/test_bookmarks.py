from django.contrib.auth.models import AnonymousUser
from mixer.backend.django import mixer

from blog.models import Blog
from core.constances import ACCESS_TYPE
from core.tests.helpers import PleioTenantTestCase
from user.models import User


class BookmarkTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)

        self.blog1 = Blog.objects.create(
            title="Test1",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True
        )

        self.blog2 = Blog.objects.create(
            title="Test2",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True
        )

        self.bookmark1 = self.blog1.add_bookmark(self.authenticatedUser)
        self.bookmark2 = self.blog2.add_bookmark(self.authenticatedUser)

    def tearDown(self):
        self.bookmark1.delete()
        self.bookmark2.delete()
        self.blog1.delete()
        self.blog2.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_bookmark_list(self):

        query = """
            {
                bookmarks (limit: 1){
                    total
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {}

        self.graphql_client.force_login(self.authenticatedUser)
        result = result = self.graphql_client.post(query, variables)

        data = result["data"]
       
        self.assertEqual(data["bookmarks"]["total"], 2)
        self.assertEqual(len(data["bookmarks"]["edges"]), 1)
        self.assertEqual(data["bookmarks"]["edges"][0]["guid"], self.bookmark2.content_object.guid)

    def test_bookmark_list_filter(self):

        query = """
            {
                bookmarks(subtype: "news") {
                    total
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {}

        self.graphql_client.force_login(self.authenticatedUser)
        result = result = self.graphql_client.post(query, variables)

        data = result["data"]
       
        self.assertEqual(data["bookmarks"]["total"], 0)

    def test_bookmark(self):

        query = """
            mutation ($bookmark: bookmarkInput!) {
                bookmark(input: $bookmark) {
                    object {
                        guid
                    }
                }
            }
        """

        variables = {
            "bookmark": {
                "guid": self.blog1.guid,
                "isAdding": False
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = result = self.graphql_client.post(query, variables)

        data = result["data"]
       
        self.assertEqual(data["bookmark"]["object"]["guid"], self.blog1.guid)

        query = """
            {
                bookmarks {
                    total
                    edges {
                        guid
                    }
                }
            }
        """

        variables = {}

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["bookmarks"]["total"], 1)
        self.assertEqual(data["bookmarks"]["edges"][0]["guid"], self.blog2.guid)
