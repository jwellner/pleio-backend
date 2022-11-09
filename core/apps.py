from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # pylint: disable=unused-import
        # pylint: disable=import-outside-toplevel
        import core.signals

        from .models.tags import register_model_for_tags
        register_model_for_tags(self.get_model('Entity'))
        register_model_for_tags(self.get_model('Group'))

        from core.lib import webpack_dev_server_is_available
        from django.conf import settings
        settings.WEBPACK_DEV_SERVER = webpack_dev_server_is_available()
