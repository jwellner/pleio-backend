from django.conf import settings
from core import config


def config_processor(request):
    """
    Add config to request context
    """
    return {
        'config': config,
        'vapid_public_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY'],
        'webpack_dev_server': settings.WEBPACK_DEV_SERVER,
    }