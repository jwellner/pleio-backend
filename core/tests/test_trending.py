from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE

class TrendingTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User)

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
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            tags=["tag_three", "tag_two"]
        )

        self.blog1.add_vote(user=self.user1, score=1)
        self.blog2.add_vote(user=self.user1, score=1)
        self.blog3.add_vote(user=self.user1, score=1)
        self.blog4.add_vote(user=self.user1, score=1)
        self.blog5.add_vote(user=self.user1, score=1)
        self.blog5.add_vote(user=self.user2, score=1)
        self.blog6.add_vote(user=self.user2, score=1)
        self.blog6.delete()


    def tearDown(self):
        self.blog1.delete()
        self.blog2.delete()
        self.blog3.delete()
        self.blog4.delete()
        self.blog5.delete()
        self.user1.delete()
        self.user2.delete()
        super().tearDown()
    
    def test_trending(self):
        query = """
            query Trending {
                trending {
                    tag
                    likes
                    __typename
                }
            }
        """

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(len(data["trending"]), 3)
        self.assertEqual(data["trending"][0]["tag"], "tag_two")
        self.assertEqual(data["trending"][0]["likes"], 6)
        self.assertEqual(data["trending"][1]["tag"], "tag_three")
        self.assertEqual(data["trending"][1]["likes"], 4)
        self.assertEqual(data["trending"][2]["tag"], "tag_one")
        self.assertEqual(data["trending"][2]["likes"], 3)
