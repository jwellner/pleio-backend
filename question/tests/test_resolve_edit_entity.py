from django.utils import timezone
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from question.models import Question
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer


class EditQuestionTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.group = mixer.blend(Group)

        self.question = Question.objects.create(
            title="Test public question",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.data = {
            "input": {
                "guid": self.question.guid,
                "title": "My first Question",
                "richDescription": "richDescription",
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
                owner {
                    guid
                }
                isClosed
                isFeatured
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...QuestionParts
                    }
                }
            }
        """

    def test_edit_question(self):

        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isClosed"], False)
        self.assertEqual(entity["isFeatured"], False) # nly with editor or admin role
        self.assertEqual(entity["featured"]["positionY"], 2)
        self.assertEqual(entity["featured"]["video"], "testVideo2")
        self.assertEqual(entity["featured"]["videoTitle"], "testVideoTitle2")
        self.assertEqual(entity["featured"]["alt"], "testAlt2")
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])

        self.question.refresh_from_db()

        self.assertEqual(entity["title"], self.question.title)
        self.assertEqual(entity["richDescription"], self.question.rich_description)
        self.assertEqual(entity["tags"], self.question.tags)
        self.assertEqual(entity["isClosed"], self.question.is_closed)
        self.assertEqual(entity["isFeatured"], False)
        self.assertEqual(entity["group"], None)
        self.assertEqual(entity["owner"]["guid"], self.authenticatedUser.guid)
        self.assertEqual(entity["timeCreated"], self.question.created_at.isoformat())


    def test_edit_question_by_admin(self):

        variables = self.data
        variables["input"]["timeCreated"] = "2018-12-10T23:00:00.000Z"
        variables["input"]["groupGuid"] = self.group.guid
        variables["input"]["ownerGuid"] = self.user2.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["editEntity"]["entity"]

        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["tags"], variables["input"]["tags"])
        self.assertEqual(entity["isClosed"], False)
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")


        self.question.refresh_from_db()

        self.assertEqual(entity["title"], self.question.title)
        self.assertEqual(entity["richDescription"], self.question.rich_description)
        self.assertEqual(entity["tags"], self.question.tags)
        self.assertEqual(entity["isClosed"], self.question.is_closed)
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")


    def test_edit_event_group_null_by_admin(self):
        variables = self.data
        variables["input"]["groupGuid"] = self.group.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["group"]["guid"], self.group.guid)

        variables["input"]["groupGuid"] = None

        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["editEntity"]["entity"]

        self.assertEqual(entity["group"], None)
