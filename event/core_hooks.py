from django.utils.translation import gettext_lazy as _


def get_entity_filters():
    yield {
        "key": "event",
        "value": _("Event"),
    }


def get_activity_filters():
    yield {
        "key": "event",
        "value": _("Event"),
    }


def get_search_filters():
    yield {
        "key": "event",
        "value": _("Event"),
        "plural": _("Events"),
    }
