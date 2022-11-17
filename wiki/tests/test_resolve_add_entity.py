from django.utils import timezone
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from wiki.models import Wiki
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class AddWikiCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.wikiPublic = Wiki.objects.create(
            title="Test public wiki",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.wikiGroupPublic = Wiki.objects.create(
            title="Test public wiki",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            group=self.group
        )

        self.data = {
            "input": {
                "type": "object",
                "subtype": "wiki",
                "title": "My first Wiki",
                "richDescription": "richDescription",
                "containerGuid": None,
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True,
                "featured": {
                    "positionY": 2,
                    "video": "testVideo2",
                    "videoTitle": "testVideoTitle2",
                    "alt": "testAlt2"
                },
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
            }
        }
        self.mutation = """
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
                    alt
                }
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...WikiParts
                    }
                }
            }
        """

    def test_add_wiki(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["hasChildren"], False)
        self.assertEqual(entity["isFeatured"], False)  # only with editor or admin role
        self.assertEqual(entity["featured"]["positionY"], 2)
        self.assertEqual(entity["featured"]["video"], "testVideo2")
        self.assertEqual(entity["featured"]["videoTitle"], "testVideoTitle2")
        self.assertEqual(entity["featured"]["alt"], "testAlt2")
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])

    def test_add_wiki_to_parent(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.wikiPublic.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["hasChildren"], False)
        self.assertEqual(entity["parent"]["guid"], self.wikiPublic.guid)

        self.wikiPublic.refresh_from_db()

        self.assertTrue(self.wikiPublic.has_children())
        self.assertEqual(self.wikiPublic.children.first().guid, entity["guid"])

    def test_add_wiki_to_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["hasChildren"], False)
        self.assertEqual(entity["parent"], None)
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)

    def test_add_wiki_to_parent_with_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.wikiGroupPublic.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["hasChildren"], False)
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["parent"]["guid"], self.wikiGroupPublic.guid)

        self.wikiGroupPublic.refresh_from_db()

        self.assertTrue(self.wikiGroupPublic.has_children())
        self.assertEqual(self.wikiGroupPublic.children.first().guid, entity["guid"])

    def test_add_minimal_entity(self):
        variables = {
            'input': {
                'title': "Simple wiki",
                'subtype': "wiki",
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertTrue(entity['canEdit'])
