from unittest import mock

from core.factories import GroupFactory
from core.tests.helpers import PleioTenantTestCase
from user.factories import UserFactory


class TestGroupModelTestCase(PleioTenantTestCase):
    NAME = "Group name"
    CONTENT = "Group content value"
    INTRO = "Group intro"
    WELCOME_MSG = "group welcome message"
    PROFILE_FIELDS_MSG = "profile fields required messsage"
    FEATURED_DATA = "FEATURED_DATA"
    PLUGINS = ['events', 'blog', 'discussion', 'questions', 'files', 'wiki', 'tasks']
    DEFAULT_TAGS = ['Bar']
    TAGS = ['Foo', 'Bar', 'Baz']
    WIDGETS = [
        {"type": "text",
         "settings": [
             {"key": "richDescription",
              "value": None,
              "richDescription": "Some rich description",
              "attachmentId": None, }
         ]}
    ]

    def setUp(self):
        super().setUp()
        self.owner = UserFactory()
        self.entity = GroupFactory(owner=self.owner,
                                   name=self.NAME,
                                   rich_description=self.CONTENT,
                                   introduction=self.INTRO,
                                   welcome_message=self.WELCOME_MSG,
                                   required_fields_message=self.PROFILE_FIELDS_MSG,
                                   plugins=self.PLUGINS,
                                   tags=self.TAGS,
                                   widget_repository=self.WIDGETS,
                                   content_presets={"defaultTags": self.DEFAULT_TAGS})

    def tearDown(self):
        self.entity.delete()
        self.owner.delete()
        super().tearDown()

    @mock.patch('core.models.group.Group.serialize_featured')
    def test_serialize(self, serialize_featured):
        serialize_featured.return_value = self.FEATURED_DATA
        serialized = self.entity.serialize()

        self.maxDiff = None

        self.assertTrue(serialize_featured.called)
        self.assertEqual(serialized, {
            'name': self.NAME,
            'ownerGuid': self.owner.guid,
            'richDescription': self.CONTENT,
            'intro': self.INTRO,
            'isIntroductionPublic': False,
            'welcomeMessage': self.WELCOME_MSG,
            'requiredProfileFieldsMessage': self.PROFILE_FIELDS_MSG,
            'icon': None,
            'isFeatured': False,
            'featured': self.FEATURED_DATA,
            'isClosed': False,
            'isMembershipOnRequest': False,
            'isLeavingGroupDisabled': False,
            'isAutoMembershipEnabled': False,
            'isSubmitUpdatesEnabled': True,
            'isHidden': False,
            'autoNotification': False,
            'plugins': self.PLUGINS,
            'tags': sorted(self.TAGS),
            'tagCategories': [],
            'defaultTags': sorted(self.DEFAULT_TAGS),
            'defaultTagCategories': [],
            'widgets': self.WIDGETS
        })

    def test_map_rich_text_fields(self):
        before = self.entity.serialize()
        expected = self.entity.serialize()
        expected['richDescription'] = "new %s" % self.CONTENT
        expected['intro'] = "new %s" % self.INTRO
        expected['widgets'][0]['settings'][0]['richDescription'] = "new Some rich description"

        self.entity.map_rich_text_fields(lambda v: "new %s" % v)
        after = self.entity.serialize()

        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)
