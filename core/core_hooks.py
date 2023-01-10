from django.utils.translation import gettext_lazy as _


def get_search_filters():
    yield {
        "key": "group",
        "value": _("Group"),
        "plural": _("Groups"),
    }
