from django.apps import AppConfig
from django.conf import settings
from core.lib import webpack_dev_server_is_available


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # pylint: disable=unused-import
        # pylint: disable=import-outside-toplevel
        settings.WEBPACK_DEV_SERVER = webpack_dev_server_is_available()
        import core.signals

        from .models.tags import register_model_for_tags
        register_model_for_tags(self.get_model('Entity'))
        register_model_for_tags(self.get_model('Group'))
