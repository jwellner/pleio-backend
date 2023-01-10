from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from question.models import Question
from user.factories import AdminFactory
from user.models import User
from mixer.backend.django import mixer
from django.utils import timezone


class AddQuestionTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.data = {
            "input": {
                "subtype": "question",
                "title": "My first Question",
                "richDescription": "richDescription",
                "accessId": 0,
                "writeAccessId": 0,
                "tags": ["tag1", "tag2"],
                "isFeatured": True,
                "featured": {
                    "positionY": 10,
                    "video": "testVideo",
                    "videoTitle": "testVideoTitle",
                    "alt": "testAlt"
                },
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
            }
        }
        self.mutation = """
            fragment QuestionParts on Question {
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
                inGroup
                featured {
                    image
                    video
                    videoTitle
                    positionY
                    alt
                }
                group {
                    guid
                }
                isClosed
                isFeatured
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...QuestionParts
                    }
                }
            }
        """

    def test_add_question(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isClosed"], False)
        self.assertEqual(entity["isFeatured"], False)  # only with editor or admin role
        self.assertEqual(entity["featured"]["positionY"], 10)
        self.assertEqual(entity["featured"]["video"], "testVideo")
        self.assertEqual(entity["featured"]["videoTitle"], "testVideoTitle")
        self.assertEqual(entity["featured"]["alt"], "testAlt")
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])

    def test_add_question_to_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)

    def test_add_minimal_entity(self):
        variables = {
            'input': {
                'title': "Simple question",
                'subtype': "question",
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertTrue(entity['canEdit'])
