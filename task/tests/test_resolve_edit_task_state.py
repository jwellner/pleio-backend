from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from ..models import Task
from core.constances import ACCESS_TYPE


class EditTaskStateTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = UserFactory()

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
                "state": "DONE",
            }
        }
        self.mutation = """
            fragment TaskParts on Task {
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
                state
            }
            mutation ($input: editTaskInput!) {
                editTask(input: $input) {
                    entity {
                    guid
                    status
                    ...TaskParts
                    }
                }
            }
        """

    def test_edit_task_state(self):
        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, self.data)
        self.taskPublic.refresh_from_db()

        data = result["data"]
        self.assertEqual(data["editTask"]["entity"]["state"], "DONE")
        self.assertEqual(data["editTask"]["entity"]["state"], self.taskPublic.state)
