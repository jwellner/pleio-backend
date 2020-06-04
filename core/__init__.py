from django.utils.functional import LazyObject

default_app_config = 'core.apps.CoreConfig'

class LazyConfig(LazyObject):
    def _setup(self):
        # pylint: disable=import-outside-toplevel
        from .base_config import Config
        self._wrapped = Config()


config = LazyConfig()
