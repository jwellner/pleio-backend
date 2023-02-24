from unittest import mock

from core.tests.helpers import PleioTenantTestCase
from user.factories import EditorFactory
from wiki.factories import WikiFactory


class TestNewsModelTestCase(PleioTenantTestCase):
    TITLE = "Demo wiki"
    CONTENT = "Demo wiki content"
    ABSTRACT = "Demo wiki abstract"
    FEATURED = "FEATURED_MEDIA"

    maxDiff = None

    def setUp(self):
        super().setUp()

        self.owner = EditorFactory()
        self.parent = WikiFactory(owner=self.owner)
        self.entity = WikiFactory(owner=self.owner,
                                  title=self.TITLE,
                                  rich_description=self.CONTENT,
                                  abstract=self.ABSTRACT,
                                  parent=self.parent)

    def tearDown(self):
        self.entity.delete()
        self.parent.delete()
        self.owner.delete()

        super().tearDown()

    @mock.patch("wiki.models.Wiki.serialize_featured")
    @mock.patch("core.models.Entity.serialize")
    def test_serialize(self, parent_serialize, serialize_featured):
        parent_serialize.return_value = {}
        serialize_featured.return_value = self.FEATURED
        serialized = self.entity.serialize()

        self.assertTrue(parent_serialize.called)
        self.assertEqual(serialized, {"title": self.TITLE,
                                      "richDescription": self.CONTENT,
                                      "abstract": self.ABSTRACT,
                                      "featured": self.FEATURED,
                                      "containerGuid": self.parent.guid})

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['richDescription'] = f"new {self.CONTENT}"
        expected['abstract'] = f"new {self.ABSTRACT}"

        self.entity.map_rich_text_fields(lambda s: "new {}".format(s))
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)
