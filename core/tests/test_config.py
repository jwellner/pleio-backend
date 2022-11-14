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
    @mock.patch('core.base_config.ConfigBackend.set')
    def test_get_name_behaviour_when_errors_occur(self, mocked_set, mocked_cache_get):
        mocked_cache_get.return_value = None

        self.assertEqual(Setting.objects.get(key='NAME').value, self.NAME)

        with mock.patch("core.models.setting.SettingManager.get") as mocked_model_get:
            mocked_model_get.side_effect = OperationalError()
            try:
                getattr(config, 'NAME')
            except Exception:
                pass

            self.assertEqual(mocked_set.call_count, 0)
