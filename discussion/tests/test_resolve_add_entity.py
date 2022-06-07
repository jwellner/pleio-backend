from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from core.constances import USER_ROLES
from mixer.backend.django import mixer


class AddDiscussionTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddDiscussionTestCase, self).setUp()
        self.anonymousUser = AnonymousUser()
        self.authenticatedUser = mixer.blend(User)
        self.editorUser = mixer.blend(User, roles=[USER_ROLES.EDITOR])
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.data = {
            "input": {
                "type": "object",
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

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["isFeatured"], False) # only editor or admin can set
        self.assertEqual(entity["featured"]["positionY"], 10)
        self.assertEqual(entity["featured"]["video"], "testVideo")
        self.assertEqual(entity["featured"]["videoTitle"], "testTitle")
        self.assertEqual(entity["featured"]["alt"], "testAlt")
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])


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

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
