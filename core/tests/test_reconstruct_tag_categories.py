import json

from mixer.backend.django import mixer

from blog.factories import BlogFactory
from core.factories import GroupFactory
from core.models import Widget
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestReconstructTagCategoriesTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.other_user = UserFactory()
        self.blog = BlogFactory(owner=self.other_user,
                                category_tags=[{"name": "Confirmation", "values": ["Yes", "No"]}
                                               ])
        self.blog2 = BlogFactory(owner=self.other_user,
                                 category_tags=[{"name": "Confirmation", "values": ["Yes"]},
                                                {"name": "Count", "values": ["One", "Two"]}
                                                ])
        self.blog3 = BlogFactory(owner=self.other_user,
                                 category_tags=[{"name": "Confirmation", "values": ["No"]}
                                                ])

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
        super().tearDown()

    def test_reconstruction(self):
        from core.utils.migrations.category_tags_reconstruct import reconstruct_tag_categories
        tag_categories = reconstruct_tag_categories()

        self.assertEqual(tag_categories, [
            {"name": "Confirmation",
             "values": ["Maybe", "No", "Yes"]},
            {"name": "Count",
             "values": ["Four", "One", "Three", "Two"]},
            {"name": "Weight",
             "values": ["Heavy", "Light"]},
        ])
