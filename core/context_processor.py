from django.conf import settings
from core import config


def config_processor(request):
    """
    Add config to request context
    """
    return {
        'config': config,
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
    }