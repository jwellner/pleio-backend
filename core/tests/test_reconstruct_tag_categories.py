import json
from unittest import mock

from mixer.backend.django import mixer

from blog.factories import BlogFactory
from core import config
from core.factories import GroupFactory
from core.models import Widget
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestReconstructTagCategoriesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()

        self.blog = BlogFactory(category_tags=[{"name": "Confirmation", "values": ["Yes", "No"]}
                                               ])
        self.blog2 = BlogFactory(category_tags=[{"name": "Confirmation", "values": ["Yes"]},
                                                {"name": "Count", "values": ["One", "Two"]}
                                                ])
        self.blog3 = BlogFactory(category_tags=[{"name": "Confirmation", "values": ["No"]}
                                                ])

        self.owner = UserFactory()
        self.group = GroupFactory(owner=self.owner,
                                  category_tags=[{"name": "Confirmation", "values": ["Yes"]}
                                                 ])
        self.group2 = GroupFactory(owner=self.owner,
                                   category_tags=[{"name": "Confirmation", "values": ["Yes"]},
                                                  {"name": "Count", "values": ["Three"]}
                                                  ])
        self.group3 = GroupFactory(owner=self.owner,
                                   category_tags=[{"name": "Confirmation", "values": ["No"]},
                                                  {"name": "Count", "values": ["One", "Three"]}
                                                  ])

        self.widget = mixer.blend(Widget, settings=[{"key": "type", "value": "misc"}])
        self.widget2 = mixer.blend(Widget, settings=[{"key": "categoryTags", 'value': json.dumps([{"name": "Weight", "values": ['Heavy', "Light"]}])},
                                                     {"key": "tagFilter", 'value': json.dumps([{"name": "Confirmation", "values": ["Maybe", "No"]},
                                                                                               {"name": "Count", "values": ["Four", "One"]}])}])
        self.widget3 = mixer.blend(Widget, settings=[])

        self.collector = self.create_collector()

    def tearDown(self):
        self.blog.delete()
        self.blog2.delete()
        self.blog3.delete()

        self.group.delete()
        self.group2.delete()
        self.group3.delete()

        self.owner.delete()

        self.widget.delete()
        self.widget2.delete()
        self.widget3.delete()

    def create_collector(self):
        from core.post_deploy import TagCategoryCollector
        return TagCategoryCollector()

    @mock.patch('core.post_deploy.TagCategoryCollector.loop_entities')
    @mock.patch('core.post_deploy.TagCategoryCollector.loop_widget_settings')
    def test_with_tag_categories_filled(self, loop_widget_settings, loop_entities):
        from core.post_deploy import reconstruct_tag_categories

        self.override_config(TAG_CATEGORIES=[{"name": "test", "values": ['One', 'Two', 'Three']}])
        reconstruct_tag_categories()
        self.assertEqual(loop_entities.call_count, 0)
        self.assertEqual(loop_widget_settings.call_count, 0)

        self.override_config(TAG_CATEGORIES=[])
        reconstruct_tag_categories()
        self.assertEqual(loop_entities.call_count, 2)
        self.assertEqual(loop_widget_settings.call_count, 1)

    def test_reconstruction(self):
        from core.post_deploy import reconstruct_tag_categories
        self.override_config(TAG_CATEGORIES=[])
        reconstruct_tag_categories()

        self.assertEqual(config.TAG_CATEGORIES, [
            {"name": "Confirmation",
             "values": ["Maybe", "No", "Yes"]},
            {"name": "Count",
             "values": ["Four", "One", "Three", "Two"]},
            {"name": "Weight",
             "values": ["Heavy", "Light"]},
        ])
