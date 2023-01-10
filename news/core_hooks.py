from django.utils.translation import gettext_lazy as _


def get_entity_filters():
    yield {
        "key": "news",
        "value": _("News"),
    }


def get_activity_filters():
    yield {
        "key": "news",
        "value": _("News"),
    }


def get_search_filters():
    yield {
        "key": "news",
        "value": _("News"),
        "plural": _("News items"),
    }
