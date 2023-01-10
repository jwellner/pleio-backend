from django.utils.translation import gettext_lazy as _


def get_entity_filters():
    yield {
        "key": "wiki",
        "value": _("Wiki"),
    }


def get_activity_filters():
    yield {
        "key": "wiki",
        "value": _("Wiki"),
    }


def get_search_filters():
    yield {
        "key": "wiki",
        "value": _("Wiki"),
        "plural": _("Wiki's")
    }
