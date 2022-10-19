from core.models import Group, Widget
from core.tests.helpers import PleioTenantTestCase
from user.models import User
from mixer.backend.django import mixer


class EditGroupWidgetTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.user1 = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.roles = ['ADMIN']
        self.admin.save()
        self.group = mixer.blend(Group, owner=self.user1)
        self.widget1 = Widget.objects.create(group=self.group, position=0,
                                             settings=[{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}])
        self.widget2 = Widget.objects.create(group=self.group, position=1,
                                             settings=[{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}])
        self.widget3 = Widget.objects.create(group=self.group, position=2,
                                             settings=[{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}])
        self.widget4 = Widget.objects.create(group=self.group, position=3,
                                             settings=[{"key": "key1", "value": "value1"}, {"key": "key2", "value": "value2"}])

    def tearDown(self):
        self.widget1.delete()
        self.widget2.delete()
        self.widget3.delete()
        self.widget4.delete()
        self.group.delete()
        self.admin.delete()
        self.user1.delete()
        super().tearDown()

    def test_edit_group_widget(self):
        mutation = """
            mutation editGroupWidget($input: editGroupWidgetInput!) {
                editGroupWidget(input: $input) {
                    entity {
                    guid
                    ... on Widget {
                        containerGuid
                        parentGuid
                        settings {
                            key
                            value
                        }
                    }
                    }
                }
            }

        """
        variables = {
            "input": {
                "guid": self.widget1.guid,
                "settings": [{"key": "key1", "value": "value1"}, {"key": "key5", "value": "value5"}, {"key": "key3", "value": "value3"}]
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertIsNotNone(data["editGroupWidget"]["entity"]["guid"])
        self.assertEqual(data["editGroupWidget"]["entity"]["containerGuid"], self.group.guid)
        self.assertEqual(data["editGroupWidget"]["entity"]["parentGuid"], self.group.guid)
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][0]["key"], "key1")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][0]["value"], "value1")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][1]["key"], "key5")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][1]["value"], "value5")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][2]["key"], "key3")
        self.assertEqual(data["editGroupWidget"]["entity"]["settings"][2]["value"], "value3")

    def test_edit_group_widget_position_move_up(self):
        mutation = """
            mutation editGroupWidget($input: editGroupWidgetInput!) {
                editGroupWidget(input: $input) {
                    entity {
                    guid
                    ... on Widget {
                        position
                    }
                    }
                }
            }

        """
        variables = {
            "input": {
                "guid": self.widget2.guid,
                "position": 2
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editGroupWidget"]["entity"]["position"], 2)
        self.assertEqual(Widget.objects.get(id=self.widget1.id).position, 0)
        self.assertEqual(Widget.objects.get(id=self.widget3.id).position, 1)
        self.assertEqual(Widget.objects.get(id=self.widget4.id).position, 3)

    def test_edit_group_widget_position_move_down(self):
        mutation = """
            mutation editGroupWidget($input: editGroupWidgetInput!) {
                editGroupWidget(input: $input) {
                    entity {
                    guid
                    ... on Widget {
                        position
                    }
                    }
                }
            }

        """
        variables = {
            "input": {
                "guid": self.widget3.guid,
                "position": 0
            }
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]

        self.assertEqual(data["editGroupWidget"]["entity"]["position"], 0)
        self.assertEqual(Widget.objects.get(id=self.widget1.id).position, 1)
        self.assertEqual(Widget.objects.get(id=self.widget2.id).position, 2)
        self.assertEqual(Widget.objects.get(id=self.widget4.id).position, 3)
