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

    def test_entity_view_blog(self):
        query = """
            query BlogItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    ...BlogDetailFragment
                    __typename
                }
            }
            fragment BlogDetailFragment on Blog {
                views
            }
        """

        variables = {
            "guid": self.blog1.guid
        }

        self.graphql_client.post(query, variables)
        self.graphql_client.post(query, variables)
        self.graphql_client.post(query, variables)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.blog1.guid)
        self.assertEqual(data["entity"]["views"], 4)

        self.graphql_client.force_login(self.owner)

        self.graphql_client.post(query, variables)
        self.graphql_client.post(query, variables)
        self.graphql_client.post(query, variables)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.blog1.guid)
        self.assertEqual(data["entity"]["views"], 5)
