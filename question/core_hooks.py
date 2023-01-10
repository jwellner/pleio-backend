from django.utils.translation import gettext_lazy as _


def get_entity_filters():
    yield {
        "key": "question",
        "value": _("Question"),
    }


def get_activity_filters():
    yield {
        "key": "question",
        "value": _("Question"),
    }


def get_search_filters():
    yield {
        "key": "question",
        "value": _("Question"),
        "plural": _("Questions"),
    }
