from django.utils.translation import gettext_lazy as _

from core import config


def get_search_filters():
    if config.COLLAB_EDITING_ENABLED:
        yield {
            "key": "pad",
            "value": _("Pad"),
            "plural": _("Pads"),
        }
