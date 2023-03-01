from unittest import mock

from core.tests.helpers import PleioTenantTestCase
from news.factories import NewsFactory
from user.factories import EditorFactory


class TestNewsModelTestCase(PleioTenantTestCase):
    TITLE = "Demo news"
    CONTENT = "Demo news content"
    ABSTRACT = "Demo news abstract"
    SOURCE = "News source description"
    FEATURED = "FEATURED_MEDIA"

    maxDiff = None

    def setUp(self):
        super().setUp()

        self.owner = EditorFactory()
        self.entity = NewsFactory(owner=self.owner,
                                  title=self.TITLE,
                                  rich_description=self.CONTENT,
                                  abstract=self.ABSTRACT,
                                  source=self.SOURCE)

    def tearDown(self):
        self.entity.delete()
        self.owner.delete()

        super().tearDown()

    @mock.patch("news.models.News.serialize_featured")
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
                                      "source": self.SOURCE})

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['richDescription'] = f"new {self.CONTENT}"
        expected['abstract'] = f"new {self.ABSTRACT}"

        self.entity.map_rich_text_fields(lambda s: "new {}".format(s))
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)
