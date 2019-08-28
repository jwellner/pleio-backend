from django.test import TestCase
from unittest.mock import patch
from core import config
from core.base_config import DEFAULT_SITE_CONFIG

class BaseConfigCase(TestCase):
    def setUp(self):
        pass
    
    def test_config(self):
        self.assertEqual(config.NAME, DEFAULT_SITE_CONFIG['NAME'][0])

        # String
        config.NAME = 'Just a test site'
        self.assertEqual(config.NAME, 'Just a test site')

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


class BaseConfigCacheCase(TestCase):
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
