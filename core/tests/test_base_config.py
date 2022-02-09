from django_tenants.test.cases import FastTenantTestCase
from unittest.mock import patch
from core import config
from core.base_config import DEFAULT_SITE_CONFIG
from core.constances import SYSTEM_TAG_CATEGORY, SYSTEM_TAGS


class BaseConfigCase(FastTenantTestCase):
    def setUp(self):
        pass

    def test_config(self):
        self.assertEqual(config.NAME, DEFAULT_SITE_CONFIG['NAME'][0])

        # String
        config.NAME = 'Pleio 2.0'
        self.assertEqual(config.NAME, 'Pleio 2.0')

        # Boolean
        config.ACHIEVEMENTS_ENABLED = False
        self.assertEqual(config.ACHIEVEMENTS_ENABLED, False)

        # Dict
        config.MENU = { "Test": "1234", "Param": { "item": "1"}}
        self.assertEqual(config.MENU, { "Test": "1234", "Param": { "item": "1"}})

        # List
        config.MENU = [1, "String", 1.23]
        self.assertEqual(config.MENU, [1, "String", 1.23])

        # Float
        config.MENU = 1.23
        self.assertEqual(config.MENU, 1.23)

        # Int
        config.MENU = 42
        self.assertEqual(config.MENU, 42)

        # Error
        with self.assertRaises(AttributeError):
            config.NON_EXISTING = False

    def test_get_tags_returns_system_tags(self):
        tag_categories = config.TAG_CATEGORIES

        system_tags = next(iter([category for category in tag_categories if category.get('name', '') == SYSTEM_TAG_CATEGORY]), None)
        self.assertIsNotNone(system_tags)
        self.assertIn(SYSTEM_TAGS.ARCHIVED, system_tags.get('values', []))

    def test_set_tags_does_not_override_system_tags(self):
        added_tag = 'extra_tag'

        config.TAG_CATEGORIES = [{'name': SYSTEM_TAG_CATEGORY, 'values': [added_tag]}]

        system_tags = next(iter([category for category in config.TAG_CATEGORIES if category.get('name', '') == SYSTEM_TAG_CATEGORY]), None)
        self.assertNotIn(added_tag, system_tags.get('values', []))
        self.assertIn(SYSTEM_TAGS.ARCHIVED, system_tags.get('values', []))

class BaseConfigCacheCase(FastTenantTestCase):
    def setUp(self):
        patcher_cache = patch('core.base_config.cache')
        self.mock_cache = patcher_cache.start()
        self.addCleanup(patcher_cache.stop)

    def test_config_cache(self):

        self.assertEqual(self.mock_cache.set.call_count, 0)
        self.assertEqual(self.mock_cache.get.call_count, 0)

        menu1 = config.MENU
        self.assertEqual(self.mock_cache.set.call_count, 0)
        self.assertEqual(self.mock_cache.get.call_count, 1)

        menu2 = config.MENU
        self.assertEqual(self.mock_cache.set.call_count, 0)
        self.assertEqual(self.mock_cache.get.call_count, 2)

        config.MENU = []
        self.assertEqual(self.mock_cache.set.call_count, 1)
        self.assertEqual(self.mock_cache.get.call_count, 2)
