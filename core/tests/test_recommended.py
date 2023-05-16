from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from news.models import News
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class RecommendedTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.blog1 = Blog.objects.create(
            title="Blog1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            is_recommended=True
        )
        self.blog2 = Blog.objects.create(
            title="Blog2",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
        )
        self.news1 = News.objects.create(
            title="News1",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
        )
        self.blog3 = Blog.objects.create(
            title="Blog3",
            owner=self.user1,
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            is_recommended=True
        )
        self.query = """
            query Recommended {
                recommended(limit: 3) {
                    total
                    edges {
                    guid
                    ... on Blog {
                        title
                        subtype
                        url
                        owner {
                        guid
                        name
                        icon
                        __typename
                        }
                        __typename
                    }
                    __typename
                    }
                    __typename
                }
            }
        """

    def tearDown(self):
        super().tearDown()

    def test_recommended(self):
        variables = {
            "limit": 1
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["recommended"]["total"], 2)
        self.assertEqual(data["recommended"]["edges"][0]["guid"], self.blog3.guid)
