from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from ..models import StatusUpdate
from core.constances import ACCESS_TYPE


class StatusUpdateTestCase(PleioTenantTestCase):

    def setUp(self):
        super(StatusUpdateTestCase, self).setUp()

        self.authenticated_user = UserFactory()

        self.statusPublic = StatusUpdate.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
            owner=self.authenticated_user,
        )

        self.statusPrivate = StatusUpdate.objects.create(
            title="Test private event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
            owner=self.authenticated_user,
        )

        self.query = """
            fragment StatusUpdateParts on StatusUpdate {
                title
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                views
                votes
                hasVoted
                isBookmarked
                isFollowing
                canBookmark
                canComment
                canVote
            }
            query GetStatusUpdat($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...StatusUpdateParts
                }
            }
        """

    def tearDown(self):
        self.statusPublic.delete()
        self.statusPrivate.delete()
        self.authenticated_user.delete()

    def test_status_update_anonymous(self):
        result = self.graphql_client.post(self.query, {
            "guid": self.statusPublic.guid
        })

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.statusPublic.guid)
        self.assertEqual(entity["title"], self.statusPublic.title)
        self.assertEqual(entity["richDescription"], self.statusPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.statusPublic.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["views"], 0)
        self.assertEqual(entity["votes"], 0)
        self.assertEqual(entity["hasVoted"], False)
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFollowing"], False)
        self.assertEqual(entity["canBookmark"], False)
        self.assertEqual(entity["canComment"], False)
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["canVote"], False)
        self.assertEqual(entity["url"], "/update/view/{}".format(self.statusPublic.guid))

        result = self.graphql_client.post(self.query, {
            "guid": self.statusPrivate.guid
        })
        self.assertEqual(result['data']['entity'], None)

    def test_status_update_private(self):
        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.query, {
            "guid": self.statusPrivate.guid
        })

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.statusPrivate.guid)
        self.assertEqual(entity["title"], self.statusPrivate.title)
        self.assertEqual(entity["richDescription"], self.statusPrivate.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.statusPrivate.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["views"], 0)
        self.assertEqual(entity["votes"], 0)
        self.assertEqual(entity["hasVoted"], False)
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFollowing"], False)
        self.assertEqual(entity["canBookmark"], True)
        self.assertEqual(entity["canComment"], True)
        self.assertEqual(entity["canVote"], True)
        self.assertEqual(entity["canEdit"], True)
