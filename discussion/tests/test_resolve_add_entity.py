from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from blog.factories import BlogFactory
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import USER_ROLES
from mixer.backend.django import mixer


class AddDiscussionTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.anonymousUser = AnonymousUser()
        self.authenticated_user = mixer.blend(User)
        self.editorUser = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.suggested_item = BlogFactory(owner=self.authenticated_user)
        self.group = mixer.blend(Group, owner=self.authenticated_user, is_membership_on_request=False)
        self.group.join(self.authenticated_user, 'owner')

        self.data = {
            "input": {
                "subtype": "discussion",
                "title": "My first discussion",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True,
                "featured": {
                    "positionY": 10,
                    "video": "testVideo",
                    "videoTitle": "testTitle",
                    "alt": "testAlt"
                },
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
                "suggestedItems": [self.suggested_item.guid]
            }
        }
        self.mutation = """
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
                featured {
                    image
                    video
                    videoTitle
                    positionY
                    alt
                }
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                isFeatured
                suggestedItems {
                    guid
                }
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...DiscussionParts
                    }
                }
            }
        """

    def test_add_discussion(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["isFeatured"], False)  # only editor or admin can set
        self.assertEqual(entity["featured"]["positionY"], 10)
        self.assertEqual(entity["featured"]["video"], "testVideo")
        self.assertEqual(entity["featured"]["videoTitle"], "testTitle")
        self.assertEqual(entity["featured"]["alt"], "testAlt")
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])
        self.assertEqual(entity["suggestedItems"], [{"guid": self.suggested_item.guid}])

    def test_add_discussion_editor(self):
        variables = self.data

        self.graphql_client.force_login(self.editorUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["isFeatured"], True)

    def test_add_discussion_to_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)

    def test_add_minimal_entity(self):
        variables = {
            'input': {
                'title': "Simple discussion",
                'subtype': "discussion",
            }
        }

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertTrue(entity['canEdit'])
