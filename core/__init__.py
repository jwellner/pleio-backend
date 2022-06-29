from contextlib import contextmanager

from django.utils.functional import LazyObject

default_app_config = 'core.apps.CoreConfig'


class LazyConfig(LazyObject):
    def _setup(self):
        # pylint: disable=import-outside-toplevel
        from .base_config import Config
        self._wrapped = Config()


config = LazyConfig()


@contextmanager
def override_local_config(**kwargs):
    recovery = {}
    try:
        for key, value in kwargs.items():
            recovery[key] = getattr(config, key, None)
            setattr(config, key, value)
        yield
    finally:
        for key, value in recovery.items():
            setattr(config, key, value)
