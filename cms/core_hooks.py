from django.utils.translation import gettext_lazy as _


def get_entity_filters():
    yield {
        "key": "page",
        "value": _("Page"),
    }


def get_activity_filters():
    yield {
        "key": "page",
        "value": _("Text page"),
    }


def get_search_filters():
    yield {
        "key": "page",
        "value": _("Page"),
        "plural": _("Pages"),
    }
