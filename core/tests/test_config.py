from unittest import mock

from django.db import OperationalError

from core import config
from core.models import Setting
from core.tests.helpers import PleioTenantTestCase


class TestConfigTestCase(PleioTenantTestCase):
    def setUp(self):
        super().setUp()

        self.NAME = "Custom name"

        Setting.objects.create(key="NAME", value=self.NAME)

    def test_get_name_from_config(self):
        self.assertEqual(config.NAME, self.NAME)

    @mock.patch('core.base_config.cache.get')
    def test_get_name_behaviour_when_errors_occur(self, mocked_cache_get):
        mocked_cache_get.return_value = None

        self.assertEqual(Setting.objects.get(key='NAME').value, self.NAME)

        with mock.patch("core.models.setting.SettingManager.get") as mocked_model_get:
            mocked_model_get.side_effect = OperationalError()
            with self.assertRaises(OperationalError):
                self.assertEqual(config.NAME, "Pleio 2.0")
            with self.assertRaises(OperationalError):
                self.assertEqual(config.NAME, "Pleio 2.0")

        self.assertEqual(Setting.objects.get(key="NAME").value, self.NAME)
