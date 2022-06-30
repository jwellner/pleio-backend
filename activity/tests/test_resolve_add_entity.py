from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory
from core.constances import COULD_NOT_ADD
from mixer.backend.django import mixer


class AddStatusUpdateTestCase(PleioTenantTestCase):

    def setUp(self):
        super(AddStatusUpdateTestCase, self).setUp()

        self.authenticated_user = UserFactory()
        self.group = mixer.blend(Group, owner=self.authenticated_user, is_membership_on_request=False)
        self.group.join(self.authenticated_user, 'owner')

        self.data = {
            "input": {
                "type": "object",
                "subtype": "status_update",
                "title": "My first StatusUpdate",
                "richDescription": "richDescription",
                "tags": ["tag1", "tag2"]
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
            }
            mutation ($input: addEntityInput!) {
                addEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...StatusUpdateParts
                    }
                }
            }
        """

    def test_add_status_update(self):
        variables = self.data

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])

    def test_add_status_update_to_group(self):
        variables = self.data
        variables["input"]["containerGuid"] = self.group.guid

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertEqual(entity["title"], variables["input"]["title"])
        self.assertEqual(entity["richDescription"], variables["input"]["richDescription"])
        self.assertEqual(entity["inGroup"], True)
        self.assertEqual(entity["group"]["guid"], self.group.guid)

    def test_add_status_update_to_updates_disabled_group(self):
        no_updates_group = mixer.blend(Group, owner=self.authenticated_user, is_submit_updates_enabled=False)
        no_updates_group.join(self.authenticated_user, 'owner')

        variables = self.data
        variables["input"]["containerGuid"] = no_updates_group.guid

        with self.assertGraphQlError(COULD_NOT_ADD):
            self.graphql_client.force_login(self.authenticated_user)
            self.graphql_client.post(self.mutation, variables)

    def test_add_minimal_entity(self):
        variables = {
            'input': {
                'title': "Simple status update",
                'subtype': "status_update",
            }
        }

        self.graphql_client.force_login(self.authenticated_user)
        result = self.graphql_client.post(self.mutation, variables)

        entity = result["data"]["addEntity"]["entity"]
        self.assertTrue(entity['canEdit'])
