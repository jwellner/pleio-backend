from unittest import mock

from cms.factories import CampagnePageFactory, TextPageFactory
from cms.models import Page
from core.tests.helpers import PleioTenantTestCase
from user.factories import EditorFactory


class Wrapper:
    class BaseTestCase(PleioTenantTestCase):
        """ Test shared functionality """

        def setUp(self):
            super().setUp()
            self.owner = EditorFactory()
            self.entity = self.entity_factory(owner=self.owner)

        def entity_factory(self, **kwargs) -> Page:
            raise NotImplementedError()

        def tearDown(self):
            self.entity.delete()
            self.owner.delete()
            super().tearDown()


class TestTextPageModelTestCase(Wrapper.BaseTestCase):
    TITLE = "Page Title"
    CONTENT = "Page content"
    POSITION = 100

    parent: Page = None

    def tearDown(self):
        self.parent.delete()
        super().tearDown()

    def entity_factory(self, **kwargs):
        if not self.parent:
            self.parent = TextPageFactory(owner=self.owner)
        return TextPageFactory(title=self.TITLE,
                               rich_description=self.CONTENT,
                               position=self.POSITION,
                               parent=self.parent,
                               **kwargs)

    @mock.patch("core.models.Entity.serialize")
    def test_serialize(self, parent_serialize):
        parent_serialize.return_value = {}
        serialized = self.entity.serialize()

        self.assertTrue(parent_serialize.called)
        self.assertEqual(serialized, {"title": self.TITLE,
                                      "richDescription": self.CONTENT,
                                      "position": self.POSITION,
                                      "parentGuid": self.parent.guid,
                                      "rows": []})

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['richDescription'] = "new %s" % self.CONTENT

        self.entity.map_rich_text_fields(lambda v: "new %s" % v)
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)


class TestCampagnePageModelTestCase(Wrapper.BaseTestCase):
    TITLE = "Page Title"
    CONTENT = "Page content"
    ROWS = [
        {"isFullWidth": False,
         "columns": [
             {"width": 1,
              "widgets": [
                  {"type": "text",
                   "settings": [
                       {"key": "title",
                        "richDescription": None,
                        "value": "This custom title",
                        "attachmentId": None},
                       {"key": "richDescription",
                        "richDescription": "Rich description",
                        "value": None,
                        "attachmentId": None}
                   ]},
                  {"type": "text",
                   "settings": [
                       {"key": "richDescription",
                        "richDescription": "Another description",
                        "value": None,
                        "attachmentId": None}
                   ]}
              ]},
             {"width": 1,
              "widgets": [
                  {"type": "demo",
                   "settings": [
                       {"key": "value",
                        "value": "42",
                        "richDescription": None,
                        "attachmentId": None}
                   ]}
              ]}
         ]},
        {"isFullWidth": True,
         "columns": [
             {"width": 2,
              "widgets": [
                  {"type": "text",
                   "settings": [
                       {"key": "richDescription",
                        "richDescription": "Yet another description",
                        "value": None,
                        "attachmentId": None}
                   ]}
              ]}
         ]}
    ]

    def entity_factory(self, **kwargs):
        return CampagnePageFactory(**kwargs,
                                   title=self.TITLE,
                                   rich_description=self.CONTENT,
                                   row_repository=self.ROWS)

    @mock.patch("core.models.Entity.serialize")
    def test_serialize(self, parent_serialize):
        parent_serialize.return_value = {}
        serialized = self.entity.serialize()

        self.assertTrue(parent_serialize.called)
        self.assertEqual(serialized, {"title": self.TITLE,
                                      "richDescription": self.CONTENT,
                                      "rows": self.ROWS,
                                      "position": 0,
                                      "parentGuid": ""})

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['rows'][0]['columns'][0]['widgets'][0]['settings'][1]['richDescription'] = "new Rich description"
        expected['rows'][0]['columns'][0]['widgets'][1]['settings'][0]['richDescription'] = "new Another description"
        expected['rows'][1]['columns'][0]['widgets'][0]['settings'][0]['richDescription'] = "new Yet another description"
        expected['richDescription'] = "new %s" % self.CONTENT

        self.maxDiff = None

        self.entity.map_rich_text_fields(lambda v: "new %s" % v)
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)

    def test_map_rich_text_fields_empty(self):
        self.entity.rich_description = ''
        self.entity.row_repository = []
        self.entity.save()
        self.entity.refresh_from_db()

        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['richDescription'] = "Foo"

        self.entity.map_rich_text_fields(lambda v: "Foo")
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)
