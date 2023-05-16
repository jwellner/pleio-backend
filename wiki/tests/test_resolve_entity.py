from core.tests.helpers import PleioTenantTestCase
from user.factories import EditorFactory, AdminFactory
from user.models import User
from wiki.factories import WikiFactory
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class WikiTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.authenticatedUser2 = mixer.blend(User)

        self.wikiPublic = WikiFactory(
            title="Test public wiki",
            rich_description="JSON to string",
            owner=self.authenticatedUser
        )

        self.wikiPrivate = WikiFactory(
            title="Test private wiki",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            parent=self.wikiPublic,
            is_featured=True
        )

        self.wikiPrivate2 = WikiFactory(
            title="Test private wiki 2",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser2.id)],
            owner=self.authenticatedUser2,
            parent=self.wikiPublic,
            is_featured=True
        )

        self.query = """
            fragment WikiParts on Wiki {
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
                url
                isBookmarked
                canBookmark
                inGroup
                group {
                    guid
                }
                hasChildren
                children {
                    guid
                }
                parent {
                    guid
                }
                isFeatured
                featured {
                    image
                    video
                    videoTitle
                    positionY
                }
            }
            query GetWiki($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...WikiParts
                }
            }
        """

    def tearDown(self):
        super().tearDown()

    def test_news_anonymous(self):
        variables = {
            "guid": self.wikiPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.wikiPublic.guid)
        self.assertEqual(entity["title"], self.wikiPublic.title)
        self.assertEqual(entity["richDescription"], self.wikiPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.wikiPublic.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFeatured"], False)
        self.assertEqual(entity["canBookmark"], False)
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["url"], "/wiki/view/{}/{}".format(self.wikiPublic.guid, slugify(self.wikiPublic.title)))
        self.assertEqual(entity["parent"], None)
        self.assertEqual(entity["hasChildren"], True)
        self.assertEqual(len(entity["children"]), 0)
        self.assertIsNotNone(entity['timePublished'])
        self.assertIsNone(entity['scheduleArchiveEntity'])
        self.assertIsNone(entity['scheduleDeleteEntity'])

        variables = {
            "guid": self.wikiPrivate.guid
        }

        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertIsNone(entity)

    def test_news_private(self):
        variables = {
            "guid": self.wikiPrivate.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.wikiPrivate.guid)
        self.assertEqual(entity["title"], self.wikiPrivate.title)
        self.assertEqual(entity["richDescription"], self.wikiPrivate.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.wikiPrivate.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["canBookmark"], True)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/wiki/view/{}/{}".format(self.wikiPrivate.guid, slugify(self.wikiPrivate.title)))
        self.assertEqual(entity["parent"]['guid'], self.wikiPublic.guid)

    def test_wiki_public(self):
        variables = {
            "guid": self.wikiPublic.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.wikiPublic.guid)
        self.assertEqual(entity["title"], self.wikiPublic.title)
        self.assertEqual(entity["richDescription"], self.wikiPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.wikiPublic.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFeatured"], False)
        self.assertEqual(entity["canBookmark"], True)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["url"], "/wiki/view/{}/{}".format(self.wikiPublic.guid, slugify(self.wikiPublic.title)))
        self.assertEqual(len(entity["children"]), 1)
        self.assertEqual(entity["children"][0]['guid'], self.wikiPrivate.guid)

    def test_wiki_editor(self):
        variables = {
            'guid': self.wikiPublic.guid
        }

        self.graphql_client.force_login(EditorFactory())
        result = self.graphql_client.post(self.query, variables)
        self.assertFalse(result['data']['entity']['canEdit'])

    def test_wiki_admin(self):
        variables = {
            'guid': self.wikiPublic.guid
        }

        self.graphql_client.force_login(AdminFactory())
        result = self.graphql_client.post(self.query, variables)
        self.assertTrue(result['data']['entity']['canEdit'])
