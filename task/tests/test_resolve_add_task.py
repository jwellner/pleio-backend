from django.utils import timezone
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class AddTaskTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddTaskTestCase, self).setUp()
        self.authenticatedUser = mixer.blend(User)
        self.group = mixer.blend(Group, owner=self.authenticatedUser, is_membership_on_request=False)
        self.group.join(self.authenticatedUser, 'owner')

        self.data = {
            "input": {
                "type": "object",
                "subtype": "task",
                "title": "My first Task",
                "richDescription": "richDescription",
                "tags": ["tag1", "tag2"],
                "accessId": 1,
                "writeAccessId": None,
                "mentions": [],
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
                state
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...TaskParts
                    }
                }
            }
        """

    def test_add_task(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result['data']['addEntity']['entity']
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["state"], "NEW")
        self.assertDateEqual(entity["timePublished"], variables['input']['timePublished'])
        self.assertDateEqual(entity["scheduleArchiveEntity"], variables['input']['scheduleArchiveEntity'])
        self.assertDateEqual(entity["scheduleDeleteEntity"], variables['input']['scheduleDeleteEntity'])

    def test_add_task_to_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result['data']['addEntity']['entity']
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["state"], "NEW")

    def test_add_minimal_entity(self):
        variables = {
            'input': {
                'title': "Simple task",
                'subtype': "task",
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.mutation, variables)
        entity = result["data"]["addEntity"]["entity"]

        self.assertTrue(entity['canEdit'])
