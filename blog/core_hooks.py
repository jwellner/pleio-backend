from django.utils.translation import gettext_lazy as _


def get_entity_filters():
    yield {
        "key": "blog",
        "value": _("Blog"),
    }


def get_activity_filters():
    yield {
        "key": "blog",
        "value": _("Blog"),
    }


def get_search_filters():
    yield {
        "key": "blog",
        "value": _("Blog"),
        "plural": _("Blogs"),
    }
