from core.tests.helpers import PleioTenantTestCase
from user.models import User
from news.models import News
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class NewsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

        self.newsPublic = News.objects.create(
            title="Test public news",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=True,
            source="source1"
        )

        self.newsPrivate = News.objects.create(
            title="Test private news",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=False,
            source="source2"
        )

        self.query = """
            fragment NewsParts on News {
                title
                richDescription
                accessId
                timeCreated
                timePublished
                scheduleArchiveEntity
                scheduleDeleteEntity
                featured {
                    image
                    video
                    videoTitle
                    positionY
                }
                isFeatured
                canEdit
                tags
                url
                views
                votes
                hasVoted
                isBookmarked
                isFollowing
                canBookmark
                owner {
                    guid
                }
                source
            }
            query GetNews($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...NewsParts
                }
            }
        """

    def tearDown(self):
        self.newsPublic.delete()
        self.newsPrivate.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_news_anonymous(self):
        variables = {
            "guid": self.newsPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.newsPublic.guid)
        self.assertEqual(entity["title"], self.newsPublic.title)
        self.assertEqual(entity["richDescription"], self.newsPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.newsPublic.created_at.isoformat())
        self.assertEqual(entity["isFeatured"], self.newsPublic.is_featured)
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["views"], 0)
        self.assertEqual(entity["votes"], 0)
        self.assertEqual(entity["hasVoted"], False)
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFollowing"], False)
        self.assertEqual(entity["canBookmark"], False)
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["owner"]["guid"], self.newsPublic.owner.guid)
        self.assertEqual(entity["url"], "/news/view/{}/{}".format(self.newsPublic.guid, slugify(self.newsPublic.title)))
        self.assertEqual(entity["source"], self.newsPublic.source)
        self.assertIsNotNone(entity["timePublished"])
        self.assertIsNone(entity["scheduleArchiveEntity"])
        self.assertIsNone(entity["scheduleDeleteEntity"])

        variables = {
            "guid": self.newsPrivate.guid
        }

        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["entity"], None)

    def test_news_private(self):
        variables = {
            "guid": self.newsPrivate.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.newsPrivate.guid)
        self.assertEqual(entity["title"], self.newsPrivate.title)
        self.assertEqual(entity["richDescription"], self.newsPrivate.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.newsPrivate.created_at.isoformat())
        self.assertEqual(entity["isFeatured"], self.newsPrivate.is_featured)
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["views"], 0)
        self.assertEqual(entity["votes"], 0)
        self.assertEqual(entity["hasVoted"], False)
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFollowing"], False)
        self.assertEqual(entity["canBookmark"], True)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["owner"]["guid"], self.newsPrivate.owner.guid)
        self.assertEqual(entity["url"], "/news/view/{}/{}".format(self.newsPrivate.guid, slugify(self.newsPrivate.title)))
        self.assertEqual(entity["source"], self.newsPrivate.source)
