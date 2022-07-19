from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class EntityViewTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = mixer.blend(User)
        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.owner,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.owner.id)]
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.owner,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.owner.id)]
        )

        self.query = """
            query ViewBlog($guid: String!, $incrementViewCount: Boolean) {
                entity(guid: $guid, incrementViewCount: $incrementViewCount) {
                    guid
                    ...BlogDetailFragment
                }
            }
            fragment BlogDetailFragment on Blog {
                views
            }
        """

        self.variables = {
            "guid": self.blog1.guid,
            "incrementViewCount": True,
        }

    def test_entity_load_blog(self):
        self.graphql_client.force_login(self.owner)
        self.variables['incrementViewCount'] = False

        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]["entity"]
        self.assertEqual(data["guid"], self.blog1.guid)
        self.assertEqual(data["views"], 0)

    def test_entity_view_blog(self):
        self.graphql_client.force_login(self.owner)

        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]["entity"]
        self.assertEqual(data["guid"], self.blog1.guid)
        self.assertEqual(data["views"], 1)

    def test_entity_view_blog_anonymous(self):
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]["entity"]
        self.assertEqual(data["guid"], self.blog1.guid)
        self.assertEqual(data["views"], 1)

    def test_entity_view_blog_multiple_anonymous(self):
        self.graphql_client.reset()
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)

        self.graphql_client.reset()
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]["entity"]
        self.assertEqual(data["guid"], self.blog1.guid)
        self.assertEqual(data["views"], 2)

    def test_entity_view_blog_mixed_anonymous(self):
        self.graphql_client.reset()
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)

        self.graphql_client.force_login(self.owner)
        self.graphql_client.post(self.query, self.variables)
        self.graphql_client.post(self.query, self.variables)
        result = self.graphql_client.post(self.query, self.variables)

        data = result["data"]["entity"]
        self.assertEqual(data["guid"], self.blog1.guid)
        self.assertEqual(data["views"], 2)
