from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE


class TopTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.user3 = mixer.blend(User)

        self.blog1 = Blog.objects.create(
            title="Test1",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_one", "tag_two", "tag_three", "tag_four", "tag_five"]
        )
        self.blog2 = Blog.objects.create(
            title="Test2",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_two"]
        )
        self.blog3 = Blog.objects.create(
            title="Test3",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_one", "tag_two", "tag_three"]
        )
        self.blog4 = Blog.objects.create(
            title="Test4",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_one", "tag_two"]
        )

        self.blog5 = Blog.objects.create(
            title="Test5",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_three", "tag_two"]
        )

        self.blog6 = Blog.objects.create(
            title="Test6",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.user3.id)],
            owner=self.user3,
            tags=["tag_three", "tag_two"]
        )

        self.blog1.add_vote(user=self.user1, score=1)
        self.blog2.add_vote(user=self.user1, score=1)
        self.blog3.add_vote(user=self.user1, score=1)
        self.blog4.add_vote(user=self.user1, score=1)
        self.blog5.add_vote(user=self.user1, score=1)
        self.blog5.add_vote(user=self.user2, score=1)
        self.blog6.add_vote(user=self.user2, score=1)
        self.blog3.delete()

    def tearDown(self):
        super().tearDown()

    def test_top(self):
        query = """
            query Top {
                top {
                    user {
                    guid
                    username
                    url
                    name
                    icon
                    __typename
                    }
                    likes
                    __typename
                }
            }
        """

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(query, {})

        data = result["data"]
        # votes > entities, gebruikers met meeste votes
        self.assertEqual(len(data["top"]), 2)
        self.assertEqual(data["top"][0]["user"]["guid"], self.user1.guid)
        self.assertEqual(data["top"][0]["likes"], 5)
        self.assertEqual(data["top"][1]["user"]["guid"], self.user3.guid)
        self.assertEqual(data["top"][1]["likes"], 1)
