from core import config


def config_processor(request):
    """
    Add config to request context
    """
    return {
        'config': config
    }