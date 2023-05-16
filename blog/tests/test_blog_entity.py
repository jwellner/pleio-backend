from unittest import mock

from blog.factories import BlogFactory
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestBlogEntityTestCase(PleioTenantTestCase):
    TITLE = "Demo title"
    CONTENT = "Demo content"
    ABSTRACT = "Demo abstract"

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.blog = BlogFactory(owner=self.owner,
                                title=self.TITLE,
                                rich_description=self.CONTENT,
                                abstract=self.ABSTRACT)

    def tearDown(self):
        super().tearDown()

    @mock.patch("core.models.Entity.serialize")
    def test_serialize(self, serialize):
        serialize.return_value = {}

        self.assertEqual(self.blog.serialize(), {
            'abstract': self.ABSTRACT,
            'featured': {"alt": "",
                         "image": None,
                         "imageGuid": None,
                         "positionY": 0,
                         "video": None,
                         "videoTitle": ""},
            'richDescription': self.CONTENT,
            'title': self.TITLE,
        })

    def test_map_rich_text_fields(self):
        before = self.blog.serialize()
        expected = self.blog.serialize()
        expected['richDescription'] = "new %s" % self.CONTENT
        expected['abstract'] = "new %s" % self.ABSTRACT

        self.blog.map_rich_text_fields(lambda v: "new %s" % v)
        snapshot = self.blog.serialize()

        self.assertNotEqual(snapshot, before)
        self.assertEqual(snapshot, expected)
