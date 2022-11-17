from core.models import Group
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory, AdminFactory
from mixer.backend.django import mixer


class AddGroupWidgetTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.user1 = UserFactory()
        self.admin = AdminFactory()
        self.group = mixer.blend(Group, owner=self.user1)

    def test_add_group_widget(self):
        mutation = """
            mutation AddGroupWidget($input: addGroupWidgetInput!) {
                addGroupWidget(input: $input) {
                    entity {
                        guid
                        containerGuid
                        parentGuid
                        type
                        settings {
                            key
                            value
                        }
                        __typename
                        }
                        __typename
                }
            }
        """
        variables = {
            "input": {
                "groupGuid": self.group.guid,
                "position": 0,
                "type": "linklist",
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}]
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertIsNotNone(data["addGroupWidget"]["entity"]["guid"])
        self.assertEqual(data["addGroupWidget"]["entity"]["containerGuid"], self.group.guid)
        self.assertEqual(data["addGroupWidget"]["entity"]["parentGuid"], self.group.guid)
        self.assertEqual(data["addGroupWidget"]["entity"]["type"], "linklist")
        self.assertEqual(data["addGroupWidget"]["entity"]["settings"][0]["key"], "key1")
