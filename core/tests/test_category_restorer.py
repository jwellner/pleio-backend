import json

from mixer.backend.django import mixer

from blog.factories import BlogFactory
from core.factories import GroupFactory
from core.models import Widget
from core.post_deploy.restore_tag_categories import CategoryRestorer
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestCategoryRestorerTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.TAG_CATEGORIES = [
            {"name": "Cat-1",
             "values": ['1-One', '1-Two', "1-Three"]},
            {"name": "Cat-2",
             "values": ['2-One', '2-Two', "2-Three"]},
            {"name": "Cat-3",
             "values": ['3-One', '3-Two', "3-Three"]},
        ]

        self.INITIAL_TAGS = ["One", "Two", "1-One", "2-Two"]
        self.INITIAL_CATEGORIES = [{'name': "Cat-1", 'values': ['1-Two']},
                                   {"name": "Other", "values": ['Three']}]

        self.EXPECTED_TAGS = ["One", "Two", "Three"]
        self.EXPECTED_CATEGORIES = [{"name": "Cat-1", "values": ["1-One", "1-Two"]},
                                    {"name": "Cat-2", "values": ["2-Two"]}]
        self.EXPECTED_WIDGET_CATEGORIES = [{'name': 'Cat-1', 'values': ['1-Two']}]

        self.owner = UserFactory()
        self.restorer = CategoryRestorer(self.TAG_CATEGORIES)

    def tearDown(self):
        self.owner.delete()
        super().tearDown()

    def test_blog_category_restorer(self):
        blog = BlogFactory(tags=self.INITIAL_TAGS,
                           category_tags=self.INITIAL_CATEGORIES,
                           owner=self.owner)

        self.restorer.process_article(blog)
        blog.refresh_from_db()

        self.assertEqual(blog.tags, self.EXPECTED_TAGS)
        self.assertEqual(blog.category_tags, self.EXPECTED_CATEGORIES)

        blog.delete()

    def test_group_restorer(self):
        group = GroupFactory(tags=self.INITIAL_TAGS,
                             category_tags=self.INITIAL_CATEGORIES,
                             owner=self.owner)

        self.restorer.process_article(group)

        group.refresh_from_db()
        self.assertEqual(group.tags, self.EXPECTED_TAGS)
        self.assertEqual(group.category_tags, self.EXPECTED_CATEGORIES)

        group.delete()

    def test_tagfilter_widget_restorer(self):
        widget: Widget = mixer.blend(Widget, settings=[{"key": 'tagFilter',
                                                        'value': json.dumps(self.INITIAL_CATEGORIES)}])

        self.restorer.process_widget(widget)

        widget.refresh_from_db()
        self.assertEqual(json.loads(widget.get_setting_value('tagFilter')), self.EXPECTED_WIDGET_CATEGORIES)

        widget.delete()

    def test_categorytag_widget_restorer(self):
        widget: Widget = mixer.blend(Widget, settings=[{"key": 'categoryTags',
                                                        'value': json.dumps(self.INITIAL_CATEGORIES)}])

        self.restorer.process_widget(widget)

        widget.refresh_from_db()
        self.assertEqual(json.loads(widget.get_setting_value('categoryTags')), self.EXPECTED_WIDGET_CATEGORIES)

        widget.delete()
