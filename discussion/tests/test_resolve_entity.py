from core.tests.helpers import PleioTenantTestCase
from user.models import User
from discussion.models import Discussion
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class EventTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

        self.discussionPublic = Discussion.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
        )

        self.discussionPrivate = Discussion.objects.create(
            title="Test private event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_featured=True
        )

        self.query = """
            fragment DiscussionParts on Discussion {
                title
                richDescription
                timeCreated
                timeUpdated
                timePublished
                scheduleArchiveEntity
                scheduleDeleteEntity
                accessId
                writeAccessId
                canEdit
                tags
                featured {
                    image
                    video
                    videoTitle
                    positionY
                    alt
                }
                url
                inGroup
                group {
                    guid
                }
                isFeatured
            }
            query GetDiscussion($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...DiscussionParts
                }
            }
        """

    def tearDown(self):
        self.discussionPublic.delete()
        self.discussionPrivate.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_event_anonymous(self):
        variables = {
            "guid": self.discussionPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.discussionPublic.guid)
        self.assertEqual(entity["title"], self.discussionPublic.title)
        self.assertEqual(entity["richDescription"], self.discussionPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.discussionPublic.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["url"], "/discussion/view/{}/{}".format(self.discussionPublic.guid, slugify(self.discussionPublic.title)))
        self.assertEqual(entity["isFeatured"], self.discussionPublic.is_featured)
        self.assertIsNotNone(entity['timePublished'])
        self.assertIsNone(entity['scheduleArchiveEntity'])
        self.assertIsNone(entity['scheduleDeleteEntity'])

        variables = {
            "guid": self.discussionPrivate.guid
        }
        result = self.graphql_client.post(self.query, variables)

        self.assertEqual(result["data"]["entity"], None)

    def test_event_private(self):
        variables = {
            "guid": self.discussionPrivate.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.discussionPrivate.guid)
        self.assertEqual(entity["title"], self.discussionPrivate.title)
        self.assertEqual(entity["richDescription"], self.discussionPrivate.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.discussionPrivate.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/discussion/view/{}/{}".format(self.discussionPrivate.guid, slugify(self.discussionPrivate.title)))
        self.assertEqual(entity["isFeatured"], self.discussionPrivate.is_featured)
