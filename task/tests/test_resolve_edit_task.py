from django.utils import timezone
from core.models import Group
from user.models import User
from ..models import Task
from core.constances import ACCESS_TYPE, USER_ROLES
from mixer.backend.django import mixer
from core.tests.helpers import PleioTenantTestCase


class EditTaskTestCase(PleioTenantTestCase):

    def setUp(self):
        super(EditTaskTestCase, self).setUp()
        self.authenticatedUser = mixer.blend(User)
        self.user2 = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.group = mixer.blend(Group)

        self.taskPublic = Task.objects.create(
            title="Test public update",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser
        )

        self.data = {
            "input": {
                "guid": self.taskPublic.guid,
                "title": "My first update",
                "richDescription": "richDescription",
                "timePublished": str(timezone.localtime()),
                "scheduleArchiveEntity": str(timezone.localtime() + timezone.timedelta(days=10)),
                "scheduleDeleteEntity": str(timezone.localtime() + timezone.timedelta(days=20)),
            }
        }
        self.mutation = """
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
                owner {
                    guid
                }
                state
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...TaskParts
                    }
                }
            }
        """

    def test_edit_task(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["editEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertDateEqual(entity["timeCreated"], self.taskPublic.created_at.isoformat())
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["state"], "NEW")
        self.assertEqual(entity["group"], None)
        self.assertEqual(entity["owner"]["guid"], self.authenticatedUser.guid)
        self.assertDateEqual(entity["timePublished"], variables["input"]["timePublished"])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables["input"]["scheduleArchiveEntity"])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables["input"]["scheduleDeleteEntity"])

        self.taskPublic.refresh_from_db()

        self.assertEqual(entity["title"], self.taskPublic.title)
        self.assertEqual(entity["richDescription"], self.taskPublic.rich_description)
        self.assertEqual(entity["state"], self.taskPublic.state)

    def test_edit_task_by_admin(self):
        variables = self.data
        variables["input"]["timeCreated"] = "2018-12-10T23:00:00.000Z"
        variables["input"]["groupGuid"] = self.group.guid
        variables["input"]["ownerGuid"] = self.user2.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result['data']['editEntity']['entity']
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["state"], "NEW")
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertDateEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

        self.taskPublic.refresh_from_db()

        self.assertEqual(entity["title"], self.taskPublic.title)
        self.assertEqual(entity["richDescription"], self.taskPublic.rich_description)
        self.assertEqual(entity["state"], self.taskPublic.state)

    def test_edit_task_group_null_by_admin(self):
        variables = self.data
        variables["input"]["groupGuid"] = self.group.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result['data']['editEntity']['entity']
        self.assertEqual(entity["group"]["guid"], self.group.guid)

        variables["input"]["groupGuid"] = None

        result = self.graphql_client.post(self.mutation, variables)

        entity = result['data']['editEntity']['entity']
        self.assertEqual(entity["group"], None)
