from core.tests.helpers import PleioTenantTestCase
from user.models import User
from ..models import Poll
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class PollTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

        self.pollPublic = Poll.objects.create(
            title="Test public poll",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.pollPrivate = Poll.objects.create(
            title="Test private poll",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.query = """
            query PollsItem($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...PollDetailFragment
                }
            }

            fragment PollDetailFragment on Poll {
                title
                url
                accessId
                timeCreated
                hasVoted
                canEdit
                choices {
                    guid
                    text
                    votes
                }
            }

        """

    def tearDown(self):
        self.pollPublic.delete()
        self.pollPrivate.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_poll_anonymous(self):
        variables = {
            "guid": self.pollPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.pollPublic.guid)
        self.assertEqual(data["entity"]["title"], self.pollPublic.title)
        self.assertEqual(data["entity"]["accessId"], 2)
        self.assertEqual(data["entity"]["timeCreated"], self.pollPublic.created_at.isoformat())
        self.assertEqual(data["entity"]["url"], "/polls/view/{}/{}".format(self.pollPublic.guid, slugify(self.pollPublic.title)))

        variables = {
            "guid": self.pollPrivate.guid
        }

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"], None)

    def test_poll_private(self):
        variables = {
            "guid": self.pollPrivate.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.pollPrivate.guid)
        self.assertEqual(data["entity"]["title"], self.pollPrivate.title)
        self.assertEqual(data["entity"]["accessId"], 0)
        self.assertEqual(data["entity"]["timeCreated"], self.pollPrivate.created_at.isoformat())
        self.assertEqual(data["entity"]["canEdit"], True)
        self.assertEqual(data["entity"]["hasVoted"], False)
        self.assertEqual(data["entity"]["choices"], [])
