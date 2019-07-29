from django.apps import AppConfig
from django.conf import settings
from .helpers import webpack_dev_server_is_available

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        settings.WEBPACK_DEV_SERVER = webpack_dev_server_is_available()
