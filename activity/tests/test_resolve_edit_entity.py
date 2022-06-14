from django.http import HttpRequest
from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from ..models import StatusUpdate
from core.constances import ACCESS_TYPE
from mixer.backend.django import mixer


class EditStatusUpdateTestCase(PleioTenantTestCase):

    def setUp(self):
        super(EditStatusUpdateTestCase, self).setUp()

        self.authenticated_user = UserFactory()
        self.user2 = UserFactory()
        self.admin = AdminFactory()
        self.group = mixer.blend(Group)

        self.statusPublic = StatusUpdate.objects.create(
            title="Test public update",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticated_user.id)],
            owner=self.authenticated_user
        )

        self.data = {
            "input": {
                "guid": self.statusPublic.guid,
                "title": "My first update",
                "richDescription": "richDescription",
                "tags": ["tag1", "tag2"],
            }
        }
        self.mutation = """
            fragment StatusUpdateParts on StatusUpdate {
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
                owner {
                    guid
                }
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...StatusUpdateParts
                    }
                }
            }
        """

    def test_edit_status_update(self):
        variables = self.data

        request = HttpRequest()
        request.user = self.authenticated_user

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result['data']['editEntity']['entity']
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])

        self.statusPublic.refresh_from_db()

        self.assertEqual(entity["title"], self.statusPublic.title)
        self.assertEqual(entity["richDescription"], self.statusPublic.rich_description)
        self.assertEqual(entity["group"], None)
        self.assertEqual(entity["owner"]["guid"], self.authenticated_user.guid)
        self.assertEqual(entity["timeCreated"], self.statusPublic.created_at.isoformat())

    def test_edit_status_update_by_admin(self):
        variables = self.data
        variables["input"]["timeCreated"] = "2018-12-10T23:00:00.000Z"
        variables["input"]["groupGuid"] = self.group.guid
        variables["input"]["ownerGuid"] = self.user2.guid

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result['data']['editEntity']['entity']
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

        self.statusPublic.refresh_from_db()

        self.assertEqual(entity["title"], self.statusPublic.title)
        self.assertEqual(entity["richDescription"], self.statusPublic.rich_description)
        self.assertEqual(entity["group"]["guid"], self.group.guid)
        self.assertEqual(entity["owner"]["guid"], self.user2.guid)
        self.assertEqual(entity["timeCreated"], "2018-12-10T23:00:00+00:00")

    def test_edit_status_update_group_null_by_admin(self):
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
