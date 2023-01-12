import uuid

from core.factories import GroupFactory
from core.models import Widget, Group
from core.post_deploy.migrate_rows_cols_widgets import do_migrate_group_widgets, do_migrate_group_link_lists
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class PostDeployTestCase(PleioTenantTestCase):
    """
    This test does not have to be maintained far after the fact.
    """
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.group: Group = GroupFactory(owner=self.owner)
        self.new_group: Group = GroupFactory(owner=self.owner, widget_repository=[{"already": "filled"}])

        self.attachment_id = str(uuid.uuid4())
        self.widget1 = Widget.objects.create(group=self.group, position=1, type="demo1",
                                             settings=[{"key": "attachment",
                                                        "attachment": self.attachment_id},
                                                       {"key": "value",
                                                        "value": "some value"},
                                                       {"key": "richDescription",
                                                        "richDescription": self.tiptap_paragraph("Some tiptap text")},
                                                       ])
        self.widget2 = Widget.objects.create(group=self.group, position=2, type="demo2",
                                             settings=[{"key": "setting",
                                                        "value": "some value"},
                                                       {"key": "setting2",
                                                        "richDescription": self.tiptap_paragraph("Some other tiptap text")}
                                                       ])
        self.widget4 = Widget.objects.create(group=self.group, position=4, type="demo3", settings=[])
        self.widget3 = Widget.objects.create(group=self.group, position=3, type="demo4",
                                             settings=[{"key": "setting",
                                                        "value": "some other value"}])

    def test_migration(self):
        # given
        before = self.group.widget_repository
        new_before = self.new_group.widget_repository
        expected_widgets = [
            {"type": "demo1",
             "settings": [
                 {"key": "attachment",
                  "value": None,
                  "richDescription": None,
                  "attachmentId": self.attachment_id},
                 {"key": "value",
                  "value": "some value",
                  "richDescription": None,
                  "attachmentId": None},
                 {"key": "richDescription",
                  "value": None,
                  "richDescription": self.tiptap_paragraph("Some tiptap text"),
                  "attachmentId": None},
             ]},
            {"type": "demo2",
             "settings": [
                 {"key": "setting",
                  "value": "some value",
                  "richDescription": None,
                  "attachmentId": None},
                 {"key": "setting2",
                  "value": None,
                  "richDescription": self.tiptap_paragraph("Some other tiptap text"),
                  "attachmentId": None},
             ]},
            {"type": "demo4",
             "settings": [
                 {"key": "setting",
                  "value": "some other value",
                  "richDescription": None,
                  "attachmentId": None},
             ]},
            {"type": "demo3",
             "settings": [
             ]},
        ]

        # when
        do_migrate_group_widgets(self.group)
        do_migrate_group_widgets(self.new_group)
        self.group.refresh_from_db()
        self.new_group.refresh_from_db()

        # then
        self.assertEqual(self.new_group.widget_repository, new_before)
        self.assertNotEqual(self.group.widget_repository, before)
        self.assertEqual(self.group.widget_repository, expected_widgets)


class TestMigrateGroupWidgetLinkListsPostDeployTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner,
                                  widget_repository=[
                                      {"type": "linklist", "settings": [{"key": "setting", "value": "setting value"}]},
                                      {"type": "demo", "settings": [{"key": "other_setting", "value": "other setting value"}]}
                                  ])

    def test_migration_works_as_expected(self):
        do_migrate_group_link_lists(self.group)

        self.group.refresh_from_db()
        self.assertEqual(self.group.widget_repository, [
            {"type": "linkList", "settings": [{"key": "setting", "value": "setting value"}]},
            {"type": "demo", "settings": [{"key": "other_setting", "value": "other setting value"}]},
        ])
