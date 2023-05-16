from core.tests.helpers import PleioTenantTestCase
from user.models import User
from blog.models import Blog
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class BlogTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedAdminUser = mixer.blend(User, roles = ['ADMIN'])

        self.featured_file = self.file_factory(self.relative_path(__file__, ['assets', 'featured.jpeg']))

        self.blogPublic = Blog.objects.create(
            title="Test public blog",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=True,
            featured_image = self.featured_file,
        )

        self.blogPrivate = Blog.objects.create(
            title="Test private blog",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_recommended=False
        )

    def tearDown(self):
        super().tearDown()

    def test_blog_anonymous(self):
        query = """
            fragment BlogParts on Blog {
                title
                richDescription
                accessId
                timeCreated
                timePublished
                scheduleArchiveEntity
                scheduleDeleteEntity
                featured {
                    image
                    imageGuid
                    video
                    videoTitle
                    positionY
                    alt
                }
                isRecommended
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
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """

        variables = {
            "guid": self.blogPublic.guid
        }

        result = self.graphql_client.post(query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.blogPublic.guid)
        self.assertEqual(entity["title"], self.blogPublic.title)
        self.assertEqual(entity["richDescription"], self.blogPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.blogPublic.created_at.isoformat())
        self.assertEqual(entity["isRecommended"], self.blogPublic.is_recommended)
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["views"], 0)
        self.assertEqual(entity["votes"], 0)
        self.assertEqual(entity["hasVoted"], False)
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFollowing"], False)
        self.assertEqual(entity["canBookmark"], False)
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["owner"]["guid"], self.blogPublic.owner.guid)
        self.assertEqual(entity["url"], "/blog/view/{}/{}".format(self.blogPublic.guid, slugify(self.blogPublic.title)))
        self.assertDateEqual(entity['timePublished'], str(self.blogPublic.published))
        self.assertIsNone(entity['scheduleArchiveEntity'])
        self.assertIsNone(entity['scheduleDeleteEntity'])
        self.assertEqual(entity['featured']['imageGuid'], self.featured_file.guid)

        variables = {
            "guid": self.blogPrivate.guid
        }

        result = self.graphql_client.post(query, variables)
        entity = result["data"]["entity"]

        self.assertIsNone(entity)
