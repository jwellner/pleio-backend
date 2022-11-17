from core.tests.helpers import PleioTenantTestCase
from user.models import User
from ..models import Task
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class TaskTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

        self.taskPublic = Task.objects.create(
            title="Test public event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            state="NEW"
        )

        self.taskPrivate = Task.objects.create(
            title="Test private event",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            state="NEW"
        )

        self.query = """
            fragment TaskParts on Task {
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
                group {
                    guid
                }
                state
            }
            query GetTask($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...TaskParts
                }
            }
        """

    def tearDown(self):
        self.taskPublic.delete()
        self.taskPrivate.delete()
        self.authenticatedUser.delete()
        super().tearDown()

    def test_task_anonymous(self):
        variables = {
            "guid": self.taskPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.taskPublic.guid)
        self.assertEqual(entity["title"], self.taskPublic.title)
        self.assertEqual(entity["richDescription"], self.taskPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.taskPublic.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["url"], "/task/view/{}/{}".format(self.taskPublic.guid, slugify(self.taskPublic.title)))
        self.assertEqual(entity["state"], self.taskPublic.state)
        self.assertIsNotNone(entity["timePublished"])
        self.assertIsNone(entity["scheduleArchiveEntity"])
        self.assertIsNone(entity["scheduleDeleteEntity"])

        variables = {
            "guid": self.taskPrivate.guid
        }
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertIsNone(entity)

    def test_task_private(self):
        variables = {
            "guid": self.taskPrivate.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result["data"]["entity"]
        self.assertEqual(entity["guid"], self.taskPrivate.guid)
        self.assertEqual(entity["title"], self.taskPrivate.title)
        self.assertEqual(entity["richDescription"], self.taskPrivate.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.taskPrivate.created_at.isoformat())
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["state"], self.taskPrivate.state)
