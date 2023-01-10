from django.utils.translation import gettext_lazy as _


def get_entity_filters():
    yield {
        "key": "discussion",
        "value": _("Discussion"),
    }


def get_activity_filters():
    yield {
        "key": "discussion",
        "value": _("Discussion"),
    }


def get_search_filters():
    yield {
        "key": "discussion",
        "value": _("Discussion"),
        "plural": _("Discussions"),
    }
